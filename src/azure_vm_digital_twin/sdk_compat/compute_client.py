"""Drop-in digital twin replacement for ``azure.mgmt.compute.ComputeManagementClient``.

This client exposes the same ``virtual_machine_sizes`` operations interface
so that code written against the real Azure SDK can be tested locally against
the E-series digital twin catalog without any Azure credentials.

Compatibility targets:
    - azure-mgmt-compute >= 30.0.0
    - azure-identity     >= 1.15.0

Usage::

    from azure_vm_digital_twin.sdk_compat import DigitalTwinComputeManagementClient

    # No credentials needed -- digital twin is fully offline
    client = DigitalTwinComputeManagementClient()
    for size in client.virtual_machine_sizes.list("eastus"):
        print(size.name, size.number_of_cores, size.memory_in_mb)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Optional

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import VMSize


@dataclass
class _VirtualMachineSize:
    """Mimics ``azure.mgmt.compute.models.VirtualMachineSize``."""

    name: str
    number_of_cores: int
    memory_in_mb: int
    os_disk_size_in_mb: int
    resource_disk_size_in_mb: int
    max_data_disk_count: int

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "number_of_cores": self.number_of_cores,
            "memory_in_mb": self.memory_in_mb,
            "os_disk_size_in_mb": self.os_disk_size_in_mb,
            "resource_disk_size_in_mb": self.resource_disk_size_in_mb,
            "max_data_disk_count": self.max_data_disk_count,
        }

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _VirtualMachineSize):
            return self.name == other.name
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"VirtualMachineSize(name={self.name!r}, "
            f"number_of_cores={self.number_of_cores}, "
            f"memory_in_mb={self.memory_in_mb})"
        )


def _vm_size_to_sdk(vm: VMSize) -> _VirtualMachineSize:
    return _VirtualMachineSize(
        name=vm.name,
        number_of_cores=vm.number_of_cores,
        memory_in_mb=vm.memory_in_mb,
        os_disk_size_in_mb=vm.os_disk_size_in_mb,
        resource_disk_size_in_mb=vm.resource_disk_size_in_mb,
        max_data_disk_count=vm.max_data_disk_count,
    )


class VirtualMachineSizesOperations:
    """Mirrors ``ComputeManagementClient.virtual_machine_sizes``.

    The real Azure SDK method signature::

        virtual_machine_sizes.list(location: str, **kwargs) -> Iterable[VirtualMachineSize]

    The digital twin ignores ``location`` (all E-series sizes are returned
    regardless of region) and yields SDK-compatible objects.
    """

    def __init__(self, catalog: ESeriesCatalog) -> None:
        self._catalog = catalog

    def list(self, location: str = "eastus", **kwargs: Any) -> Iterator[_VirtualMachineSize]:
        """List available E-series VM sizes.

        Args:
            location: Azure region (accepted for API compatibility but ignored
                      by the digital twin).
        """
        for vm in self._catalog.list():
            yield _vm_size_to_sdk(vm)


class DigitalTwinComputeManagementClient:
    """Offline digital twin of ``azure.mgmt.compute.ComputeManagementClient``.

    Provides the ``virtual_machine_sizes`` attribute with the same iteration
    interface as the real client, enabling SDK-compatible code to run against
    the E-series catalog without Azure credentials or network access.

    Args:
        credential: Accepted for API compatibility; ignored by the twin.
        subscription_id: Accepted for API compatibility; ignored by the twin.
        series_filter: Optionally limit to specific E sub-series.
    """

    def __init__(
        self,
        credential: Any = None,
        subscription_id: str = "digital-twin",
        series_filter: Optional[list[str]] = None,
    ) -> None:
        self._catalog = ESeriesCatalog(series_filter=series_filter)
        self.virtual_machine_sizes = VirtualMachineSizesOperations(self._catalog)

    @property
    def catalog(self) -> ESeriesCatalog:
        """Access the underlying E-series catalog for extended queries."""
        return self._catalog

    def close(self) -> None:
        """No-op for API compatibility."""

    def __enter__(self) -> "DigitalTwinComputeManagementClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
