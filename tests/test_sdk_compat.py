"""Tests for the SDK compatibility layer.

Validates that the digital twin client exposes the same interface patterns
as ``azure.mgmt.compute.ComputeManagementClient`` so that code written
against the real SDK can be tested offline against the E-series catalog.
"""

import pytest

from azure_vm_digital_twin.sdk_compat import (
    DigitalTwinComputeManagementClient,
    VirtualMachineSizesOperations,
)


class TestDigitalTwinComputeClient:
    def test_instantiate_without_credentials(self):
        client = DigitalTwinComputeManagementClient()
        assert client is not None

    def test_instantiate_with_dummy_credentials(self):
        client = DigitalTwinComputeManagementClient(
            credential="fake-credential",
            subscription_id="00000000-0000-0000-0000-000000000000",
        )
        assert client is not None

    def test_context_manager(self):
        with DigitalTwinComputeManagementClient() as client:
            sizes = list(client.virtual_machine_sizes.list("eastus"))
            assert len(sizes) > 0

    def test_virtual_machine_sizes_attribute(self):
        client = DigitalTwinComputeManagementClient()
        assert isinstance(client.virtual_machine_sizes, VirtualMachineSizesOperations)

    def test_list_returns_iterable(self):
        client = DigitalTwinComputeManagementClient()
        sizes = client.virtual_machine_sizes.list("eastus")
        first = next(sizes)
        assert hasattr(first, "name")
        assert hasattr(first, "number_of_cores")
        assert hasattr(first, "memory_in_mb")

    def test_list_location_is_ignored(self):
        client = DigitalTwinComputeManagementClient()
        east = list(client.virtual_machine_sizes.list("eastus"))
        west = list(client.virtual_machine_sizes.list("westeurope"))
        assert len(east) == len(west)

    def test_vm_size_has_sdk_fields(self):
        client = DigitalTwinComputeManagementClient()
        for size in client.virtual_machine_sizes.list("eastus"):
            assert isinstance(size.name, str)
            assert isinstance(size.number_of_cores, int)
            assert isinstance(size.memory_in_mb, int)
            assert isinstance(size.os_disk_size_in_mb, int)
            assert isinstance(size.resource_disk_size_in_mb, int)
            assert isinstance(size.max_data_disk_count, int)
            break  # one is enough

    def test_as_dict(self):
        client = DigitalTwinComputeManagementClient()
        size = next(client.virtual_machine_sizes.list("eastus"))
        d = size.as_dict()
        expected_keys = {
            "name", "number_of_cores", "memory_in_mb",
            "os_disk_size_in_mb", "resource_disk_size_in_mb",
            "max_data_disk_count",
        }
        assert expected_keys == set(d.keys())

    def test_series_filter(self):
        client = DigitalTwinComputeManagementClient(series_filter=["Esv7"])
        sizes = list(client.virtual_machine_sizes.list("eastus"))
        assert len(sizes) > 0
        # All should be Esv7 names
        assert all("_v7" in s.name for s in sizes)

    def test_catalog_access(self):
        client = DigitalTwinComputeManagementClient()
        catalog = client.catalog
        assert catalog.count() > 0


class TestSDKPatternCompatibility:
    """Ensure code patterns from azure-mgmt-compute docs work unchanged."""

    def test_typical_list_pattern(self):
        """Pattern from Azure SDK quickstart: list sizes and find one >= N cores."""
        client = DigitalTwinComputeManagementClient()
        suitable = [
            size for size in client.virtual_machine_sizes.list("eastus")
            if size.number_of_cores >= 8 and size.memory_in_mb >= 64 * 1024
        ]
        assert len(suitable) > 0

    def test_hardware_profile_pattern(self):
        """Simulate building a hardware_profile dict from listed sizes."""
        client = DigitalTwinComputeManagementClient()
        size = next(client.virtual_machine_sizes.list("eastus"))
        hardware_profile = {"vm_size": size.name}
        assert hardware_profile["vm_size"].startswith("Standard_E")

    def test_size_comparison(self):
        """VM sizes with the same name should be equal."""
        client = DigitalTwinComputeManagementClient()
        sizes_a = list(client.virtual_machine_sizes.list("eastus"))
        sizes_b = list(client.virtual_machine_sizes.list("westus"))
        assert sizes_a[0] == sizes_b[0]

    def test_repr(self):
        client = DigitalTwinComputeManagementClient()
        size = next(client.virtual_machine_sizes.list("eastus"))
        r = repr(size)
        assert "VirtualMachineSize" in r
        assert size.name in r
