"""Tests for the SDK compatibility layer.

Validates that the digital twin client exposes the same interface patterns
as ``azure.mgmt.compute.ComputeManagementClient`` so that code written
against the real SDK can be tested offline against E-series VMs.
"""

import pytest

from azure_vm_digital_twin.sdk_compat import (
    DigitalTwinComputeManagementClient,
    VirtualMachinesOperations,
)
from azure_vm_digital_twin.models import VMPowerState


class TestVirtualMachineSizes:
    def test_instantiate_without_credentials(self):
        client = DigitalTwinComputeManagementClient()
        assert client is not None

    def test_instantiate_with_dummy_credentials(self):
        client = DigitalTwinComputeManagementClient(
            credential="dummy", subscription_id="sub-123"
        )
        assert client.subscription_id == "sub-123"

    def test_context_manager(self):
        with DigitalTwinComputeManagementClient() as client:
            sizes = list(client.virtual_machine_sizes.list("eastus"))
            assert len(sizes) > 0

    def test_list_returns_iterable(self):
        client = DigitalTwinComputeManagementClient()
        sizes = list(client.virtual_machine_sizes.list("eastus"))
        assert len(sizes) > 50

    def test_list_location_is_ignored(self):
        client = DigitalTwinComputeManagementClient()
        east = list(client.virtual_machine_sizes.list("eastus"))
        west = list(client.virtual_machine_sizes.list("westeurope"))
        assert len(east) == len(west)

    def test_vm_size_has_sdk_fields(self):
        client = DigitalTwinComputeManagementClient()
        size = next(iter(client.virtual_machine_sizes.list("eastus")))
        assert hasattr(size, "name")
        assert hasattr(size, "number_of_cores")
        assert hasattr(size, "memory_in_mb")
        assert hasattr(size, "os_disk_size_in_mb")
        assert hasattr(size, "resource_disk_size_in_mb")
        assert hasattr(size, "max_data_disk_count")

    def test_as_dict(self):
        client = DigitalTwinComputeManagementClient()
        size = next(iter(client.virtual_machine_sizes.list("eastus")))
        d = size.as_dict()
        assert isinstance(d, dict)
        assert set(d.keys()) == {
            "name", "number_of_cores", "memory_in_mb",
            "os_disk_size_in_mb", "resource_disk_size_in_mb", "max_data_disk_count",
        }


class TestVirtualMachinesOperations:
    def test_has_virtual_machines_attribute(self):
        client = DigitalTwinComputeManagementClient()
        assert hasattr(client, "virtual_machines")
        assert isinstance(client.virtual_machines, VirtualMachinesOperations)

    def test_begin_create_or_update(self):
        with DigitalTwinComputeManagementClient() as client:
            poller = client.virtual_machines.begin_create_or_update(
                "my-rg", "sdk-vm",
                {"hardware_profile": {"vm_size": "Standard_E8s_v5"}},
            )
            assert poller.done()
            vm = poller.result()
            assert vm.name == "sdk-vm"
            assert vm.vm_size.name == "Standard_E8s_v5"

    def test_begin_create_azure_style_params(self):
        """Test with Azure-style nested parameter format."""
        with DigitalTwinComputeManagementClient() as client:
            poller = client.virtual_machines.begin_create_or_update(
                "rg", "az-vm",
                {
                    "properties": {
                        "hardwareProfile": {"vmSize": "Standard_E16s_v5"},
                    },
                    "tags": {"env": "test"},
                },
            )
            vm = poller.result()
            assert vm.vm_size.number_of_cores == 16

    def test_get_vm(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg", "get-test",
                {"hardware_profile": {"vm_size": "Standard_E4s_v5"}},
            )
            vm = client.virtual_machines.get("rg", "get-test")
            assert vm is not None
            assert vm.name == "get-test"

    def test_get_nonexistent_returns_none(self):
        client = DigitalTwinComputeManagementClient()
        assert client.virtual_machines.get("rg", "nope") is None

    def test_begin_deallocate(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg", "dealloc-test",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            poller = client.virtual_machines.begin_deallocate("rg", "dealloc-test")
            assert poller.status() == "Succeeded"
            vm = client.virtual_machines.get("rg", "dealloc-test")
            assert vm.power_state == VMPowerState.DEALLOCATED

    def test_begin_delete(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg", "del-test",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            client.virtual_machines.begin_delete("rg", "del-test")
            assert client.virtual_machines.get("rg", "del-test") is None

    def test_list_vms_by_resource_group(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg-a", "vm-a",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            client.virtual_machines.begin_create_or_update(
                "rg-b", "vm-b",
                {"hardware_profile": {"vm_size": "Standard_E4s_v5"}},
            )
            rg_a_vms = list(client.virtual_machines.list("rg-a"))
            assert len(rg_a_vms) == 1
            assert rg_a_vms[0].name == "vm-a"

    def test_list_all(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg", "vm-1",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            client.virtual_machines.begin_create_or_update(
                "rg", "vm-2",
                {"hardware_profile": {"vm_size": "Standard_E4s_v5"}},
            )
            all_vms = list(client.virtual_machines.list_all())
            assert len(all_vms) >= 2

    def test_instance_view(self):
        with DigitalTwinComputeManagementClient() as client:
            client.virtual_machines.begin_create_or_update(
                "rg", "iv-test",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            view = client.virtual_machines.instance_view("rg", "iv-test")
            assert "statuses" in view
            codes = [s["code"] for s in view["statuses"]]
            assert any("PowerState" in c for c in codes)

    def test_poller_interface(self):
        """Test that LROPoller has the right methods."""
        with DigitalTwinComputeManagementClient() as client:
            poller = client.virtual_machines.begin_create_or_update(
                "rg", "poller-test",
                {"hardware_profile": {"vm_size": "Standard_E2s_v5"}},
            )
            assert poller.done() is True
            assert poller.status() == "Succeeded"
            poller.wait()  # should not raise
            assert poller.result() is not None


class TestSDKPatternCompatibility:
    """Test that real-world Azure SDK code patterns work with the twin."""

    def test_typical_list_sizes_pattern(self):
        """Pattern: for size in client.virtual_machine_sizes.list(loc)"""
        client = DigitalTwinComputeManagementClient()
        suitable = []
        for size in client.virtual_machine_sizes.list("eastus"):
            if size.number_of_cores >= 16 and size.memory_in_mb >= 128 * 1024:
                suitable.append(size)
        assert len(suitable) > 0

    def test_typical_create_vm_pattern(self):
        """Pattern: poller = client.virtual_machines.begin_create_or_update(...)"""
        with DigitalTwinComputeManagementClient() as client:
            params = {
                "hardware_profile": {"vm_size": "Standard_E32s_v5"},
                "tags": {"workload": "database"},
            }
            poller = client.virtual_machines.begin_create_or_update(
                "prod-rg", "db-server", params
            )
            vm = poller.result()
            assert vm.vm_size.number_of_cores == 32
            assert vm.vm_size.memory_in_mb == 256 * 1024

    def test_typical_lifecycle_pattern(self):
        """Pattern: create -> start -> stop -> delete"""
        with DigitalTwinComputeManagementClient() as client:
            # Create
            client.virtual_machines.begin_create_or_update(
                "rg", "lifecycle",
                {"hardware_profile": {"vm_size": "Standard_E4s_v5"}},
            ).result()

            # Get status
            vm = client.virtual_machines.get("rg", "lifecycle")
            assert vm.is_running

            # Deallocate
            client.virtual_machines.begin_deallocate("rg", "lifecycle").wait()
            vm = client.virtual_machines.get("rg", "lifecycle")
            assert vm.power_state == VMPowerState.DEALLOCATED

            # Start again
            client.virtual_machines.begin_start("rg", "lifecycle").wait()
            vm = client.virtual_machines.get("rg", "lifecycle")
            assert vm.is_running

            # Delete
            client.virtual_machines.begin_delete("rg", "lifecycle").wait()
            assert client.virtual_machines.get("rg", "lifecycle") is None
