"""Tests for the simulation engine (resource governor, VM instance manager)."""

import pytest

from azure_vm_digital_twin.simulator.resource_governor import (
    AppliedConstraints,
    ResourceGovernor,
)
from azure_vm_digital_twin.simulator.vm_instance import VMInstanceManager
from azure_vm_digital_twin.simulator.network_governor import NetworkGovernor
from azure_vm_digital_twin.models import VMPowerState


class TestResourceGovernor:
    def test_enforcement_method(self):
        gov = ResourceGovernor()
        assert gov.enforcement_method in ("cgroupv2", "process")

    def test_create_sandbox(self):
        gov = ResourceGovernor()
        constraints = gov.create_sandbox(
            name="test-sandbox",
            cpu_cores=4,
            memory_mb=32 * 1024,
            iops_limit=6400,
            throughput_mbps=145,
        )
        assert constraints.cpu_cores == 4
        assert constraints.memory_limit_bytes == 32 * 1024 * 1024 * 1024
        assert constraints.io_max_iops == 6400
        assert constraints.method in ("cgroupv2", "process")
        gov.destroy_sandbox("test-sandbox")

    def test_constraints_as_dict(self):
        constraints = AppliedConstraints(
            cpu_cores=8,
            cpu_quota_us=800_000,
            memory_limit_bytes=64 * 1024 * 1024 * 1024,
            io_max_iops=12800,
            method="process",
        )
        d = constraints.as_dict()
        assert d["cpu_cores"] == 8
        assert d["memory_limit_mb"] == 64 * 1024
        assert d["io_max_iops"] == 12800
        assert d["enforcement"] == "process"

    def test_destroy_nonexistent_sandbox_is_safe(self):
        gov = ResourceGovernor()
        gov.destroy_sandbox("does-not-exist")  # Should not raise

    def test_get_constraints(self):
        gov = ResourceGovernor()
        gov.create_sandbox("lookup", cpu_cores=2, memory_mb=16 * 1024)
        c = gov.get_constraints("lookup")
        assert c is not None
        assert c.cpu_cores == 2
        gov.destroy_sandbox("lookup")

    def test_get_constraints_after_destroy(self):
        gov = ResourceGovernor()
        gov.create_sandbox("tmp", cpu_cores=2, memory_mb=16 * 1024)
        gov.destroy_sandbox("tmp")
        assert gov.get_constraints("tmp") is None

    def test_destroy_all(self):
        gov = ResourceGovernor()
        gov.create_sandbox("a", cpu_cores=2, memory_mb=8192)
        gov.create_sandbox("b", cpu_cores=4, memory_mb=16384)
        gov.destroy_all()
        assert gov.get_constraints("a") is None
        assert gov.get_constraints("b") is None

    def test_read_cpu_stats(self):
        gov = ResourceGovernor()
        gov.create_sandbox("stat-test", cpu_cores=2, memory_mb=8192)
        stats = gov.read_cpu_stats("stat-test")
        assert "throttled_periods" in stats
        assert "throttled_time_us" in stats
        gov.destroy_sandbox("stat-test")

    def test_read_memory_stats(self):
        gov = ResourceGovernor()
        gov.create_sandbox("mem-stat", cpu_cores=2, memory_mb=8192)
        stats = gov.read_memory_stats("mem-stat")
        assert "current_bytes" in stats
        assert "oom_kill" in stats
        gov.destroy_sandbox("mem-stat")


class TestNetworkGovernor:
    def test_instantiation(self):
        ng = NetworkGovernor(interface="lo")
        assert isinstance(ng.available, bool)

    def test_remove_nonexistent_is_safe(self):
        ng = NetworkGovernor(interface="lo")
        ng.remove_limit("nope")  # Should not raise

    def test_remove_all(self):
        ng = NetworkGovernor(interface="lo")
        ng.remove_all()  # Should not raise


class TestVMInstanceManager:
    def test_create_instance(self):
        mgr = VMInstanceManager()
        vm = mgr.create("mgr-test", "Standard_E4s_v5")
        assert vm.name == "mgr-test"
        assert vm.power_state == VMPowerState.STOPPED
        mgr.cleanup()

    def test_start_instance(self):
        mgr = VMInstanceManager()
        mgr.create("start-test", "Standard_E8s_v5")
        constraints = mgr.start("start-test")
        vm = mgr.get("start-test")
        assert vm.is_running
        assert constraints.cpu_cores == 8
        mgr.cleanup()

    def test_stop_instance(self):
        mgr = VMInstanceManager()
        mgr.create("stop-test", "Standard_E4s_v5")
        mgr.start("stop-test")
        mgr.stop("stop-test")
        vm = mgr.get("stop-test")
        assert vm.power_state == VMPowerState.STOPPED
        mgr.cleanup()

    def test_delete_instance(self):
        mgr = VMInstanceManager()
        mgr.create("del-test", "Standard_E2s_v5")
        mgr.delete("del-test")
        assert mgr.get("del-test") is None
        mgr.cleanup()

    def test_resize_instance(self):
        mgr = VMInstanceManager()
        mgr.create("resize-test", "Standard_E4s_v5")
        vm = mgr.resize("resize-test", "Standard_E32s_v5")
        assert vm.vm_size.number_of_cores == 32
        mgr.cleanup()

    def test_list_instances(self):
        mgr = VMInstanceManager()
        mgr.create("vm-1", "Standard_E2s_v5")
        mgr.create("vm-2", "Standard_E4s_v5")
        vms = mgr.list_instances()
        assert len(vms) == 2
        mgr.cleanup()

    def test_cleanup_releases_all(self):
        mgr = VMInstanceManager()
        mgr.create("c1", "Standard_E2s_v5")
        mgr.start("c1")
        mgr.cleanup()
        assert mgr.list_instances() == []
