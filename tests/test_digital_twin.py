"""Tests for the AzureESeriesDigitalTwin simulation orchestrator."""

import pytest

from azure_vm_digital_twin.digital_twin import AzureESeriesDigitalTwin
from azure_vm_digital_twin.models import VMPowerState


class TestVMLifecycle:
    def test_create_vm(self):
        twin = AzureESeriesDigitalTwin()
        vm = twin.create_vm("test-01", "Standard_E8s_v5")
        assert vm.name == "test-01"
        assert vm.vm_size.name == "Standard_E8s_v5"
        assert vm.vm_size.number_of_cores == 8
        assert vm.vm_size.memory_in_mb == 64 * 1024
        assert vm.power_state == VMPowerState.STOPPED
        twin.cleanup()

    def test_create_vm_bad_size_raises(self):
        twin = AzureESeriesDigitalTwin()
        with pytest.raises(ValueError, match="Unknown VM size"):
            twin.create_vm("bad", "Standard_FAKE_v99")
        twin.cleanup()

    def test_create_duplicate_raises(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("dup", "Standard_E4s_v5")
        with pytest.raises(ValueError, match="already exists"):
            twin.create_vm("dup", "Standard_E4s_v5")
        twin.cleanup()

    def test_start_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("start-test", "Standard_E16s_v5")
        constraints = twin.start_vm("start-test")
        vm = twin.get_vm("start-test")
        assert vm.is_running
        assert constraints.cpu_cores == 16
        assert constraints.memory_limit_bytes == 128 * 1024 * 1024 * 1024
        twin.cleanup()

    def test_stop_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("stop-test", "Standard_E4s_v5")
        twin.start_vm("stop-test")
        twin.stop_vm("stop-test")
        vm = twin.get_vm("stop-test")
        assert vm.power_state == VMPowerState.STOPPED
        assert not vm.is_running
        twin.cleanup()

    def test_deallocate_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("dealloc", "Standard_E2s_v5")
        twin.start_vm("dealloc")
        twin.deallocate_vm("dealloc")
        vm = twin.get_vm("dealloc")
        assert vm.power_state == VMPowerState.DEALLOCATED
        twin.cleanup()

    def test_delete_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("del-test", "Standard_E2s_v5")
        twin.delete_vm("del-test")
        assert twin.get_vm("del-test") is None
        twin.cleanup()

    def test_resize_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("resize", "Standard_E4s_v5")
        vm = twin.resize_vm("resize", "Standard_E16s_v5")
        assert vm.vm_size.name == "Standard_E16s_v5"
        assert vm.vm_size.number_of_cores == 16
        twin.cleanup()

    def test_resize_running_raises(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("resize-run", "Standard_E4s_v5")
        twin.start_vm("resize-run")
        with pytest.raises(RuntimeError, match="stopped before resizing"):
            twin.resize_vm("resize-run", "Standard_E16s_v5")
        twin.cleanup()

    def test_list_vms(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("a", "Standard_E2s_v5")
        twin.create_vm("b", "Standard_E4s_v5")
        vms = twin.list_vms()
        names = {vm.name for vm in vms}
        assert names == {"a", "b"}
        twin.cleanup()


class TestWorkloadExecution:
    def test_run_simple_command(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("work-vm", "Standard_E4s_v5")
        twin.start_vm("work-vm")

        result = twin.run_workload("work-vm", ["echo", "hello world"])
        assert result.passed
        assert result.metrics.exit_code == 0
        assert "hello world" in result.stdout
        assert result.vm_size.name == "Standard_E4s_v5"
        twin.cleanup()

    def test_run_script(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("script-vm", "Standard_E8s_v5")
        twin.start_vm("script-vm")

        result = twin.run_script("script-vm", "echo $((2 + 3))")
        assert result.passed
        assert "5" in result.stdout
        twin.cleanup()

    def test_run_on_stopped_vm_raises(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("stopped-vm", "Standard_E2s_v5")
        with pytest.raises(RuntimeError, match="not running"):
            twin.run_workload("stopped-vm", ["echo", "fail"])
        twin.cleanup()

    def test_run_nonexistent_vm_raises(self):
        twin = AzureESeriesDigitalTwin()
        with pytest.raises(ValueError, match="does not exist"):
            twin.run_workload("nope", ["echo"])
        twin.cleanup()

    def test_run_failing_command(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("fail-vm", "Standard_E4s_v5")
        twin.start_vm("fail-vm")

        result = twin.run_workload("fail-vm", ["false"])
        assert not result.passed
        assert result.metrics.exit_code != 0
        twin.cleanup()

    def test_workload_with_timeout(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("timeout-vm", "Standard_E2s_v5")
        twin.start_vm("timeout-vm")

        result = twin.run_workload(
            "timeout-vm", ["sleep", "60"], timeout=1.0
        )
        # Should be killed by timeout
        assert result.metrics.exit_code != 0
        twin.cleanup()

    def test_workload_records_on_vm(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("rec-vm", "Standard_E4s_v5")
        twin.start_vm("rec-vm")

        twin.run_workload("rec-vm", ["echo", "run1"])
        twin.run_workload("rec-vm", ["echo", "run2"])

        vm = twin.get_vm("rec-vm")
        assert len(vm.workload_results) == 2
        twin.cleanup()

    def test_metrics_has_duration(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("dur-vm", "Standard_E4s_v5")
        twin.start_vm("dur-vm")

        result = twin.run_workload("dur-vm", ["sleep", "0.2"])
        assert result.metrics.duration_seconds >= 0.1
        twin.cleanup()

    def test_enforced_constraints_in_result(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("constr-vm", "Standard_E16s_v5")
        twin.start_vm("constr-vm")

        result = twin.run_workload("constr-vm", ["echo", "ok"])
        assert "cpu_cores" in result.enforced_constraints
        assert result.enforced_constraints["cpu_cores"] == 16
        assert "memory_limit_mb" in result.enforced_constraints
        twin.cleanup()

    def test_cpu_intensive_workload_produces_metrics(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("cpu-vm", "Standard_E2s_v5")
        twin.start_vm("cpu-vm")

        result = twin.run_workload(
            "cpu-vm",
            ["python3", "-c", "sum(range(10_000_000))"],
        )
        assert result.passed
        assert result.metrics.duration_seconds > 0
        assert result.metrics.vm_size_name == "Standard_E2s_v5"
        twin.cleanup()


class TestReporting:
    def test_generate_report(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("rpt-vm", "Standard_E8s_v5")
        twin.start_vm("rpt-vm")
        twin.run_workload("rpt-vm", ["echo", "test"])

        report = twin.generate_report("rpt-vm")
        assert "Standard_E8s_v5" in report
        assert "rpt-vm" in report
        assert "Workload #1" in report
        assert "PASSED" in report
        twin.cleanup()

    def test_generate_report_no_workloads(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("empty-vm", "Standard_E4s_v5")
        report = twin.generate_report("empty-vm")
        assert "No workloads" in report
        twin.cleanup()

    def test_generate_report_unknown_vm(self):
        twin = AzureESeriesDigitalTwin()
        report = twin.generate_report("ghost")
        assert "not found" in report
        twin.cleanup()

    def test_workload_result_summary(self):
        twin = AzureESeriesDigitalTwin()
        twin.create_vm("sum-vm", "Standard_E4s_v5")
        twin.start_vm("sum-vm")
        result = twin.run_workload("sum-vm", ["echo", "test"])

        summary = result.summary()
        assert "PASSED" in summary
        assert "Standard_E4s_v5" in summary
        assert "CPU:" in summary
        assert "Memory:" in summary
        assert "I/O:" in summary
        twin.cleanup()


class TestVMInstance:
    def test_vm_id_format(self):
        twin = AzureESeriesDigitalTwin()
        vm = twin.create_vm("id-test", "Standard_E2s_v5")
        assert "/subscriptions/digital-twin/" in vm.id
        assert "id-test" in vm.id
        twin.cleanup()

    def test_vm_as_sdk_dict(self):
        twin = AzureESeriesDigitalTwin()
        vm = twin.create_vm("dict-test", "Standard_E4s_v5")
        d = vm.as_sdk_dict()
        assert d["name"] == "dict-test"
        assert d["properties"]["hardwareProfile"]["vmSize"] == "Standard_E4s_v5"
        assert "instanceView" in d["properties"]
        twin.cleanup()
