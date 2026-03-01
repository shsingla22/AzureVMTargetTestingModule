"""Drop-in replacement for ``azure.mgmt.compute.ComputeManagementClient``.

Provides the same attribute / method surface that real Azure SDK code
uses, but backed by the digital-twin simulation engine.  Code written
against the real SDK can switch to this client with a one-line change
and run against simulated E-series VMs without Azure credentials.

Compatibility targets:
    - azure-mgmt-compute >= 30.0.0
    - azure-identity     >= 1.15.0

Supported operations
--------------------

``client.virtual_machine_sizes.list(location)``
    List all E-series VM sizes (mirrors real SDK).

``client.virtual_machines.begin_create_or_update(rg, name, params)``
    Create a digital-twin VM and enforce its SKU constraints.

``client.virtual_machines.get(rg, name)``
    Get VM state, power status, and workload results.

``client.virtual_machines.begin_start(rg, name)``
    Start the VM (activate cgroup sandbox).

``client.virtual_machines.begin_deallocate(rg, name)``
    Stop the VM (release constraints).

``client.virtual_machines.begin_delete(rg, name)``
    Delete the VM.

``client.virtual_machines.list(rg)``
    List all VMs in a resource group.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Optional

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import VMInstance, VMSize
from azure_vm_digital_twin.simulator.vm_instance import VMInstanceManager
from azure_vm_digital_twin.workload.runner import WorkloadRunner


# ---------------------------------------------------------------------------
# VirtualMachineSize (mirrors azure.mgmt.compute.models.VirtualMachineSize)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# LROPoller stub (mirrors azure.core.polling.LROPoller)
# ---------------------------------------------------------------------------

class _LROPoller:
    """Stub for long-running operation pollers.

    In the digital twin everything completes synchronously, so result()
    just returns the value immediately.
    """

    def __init__(self, result: Any = None) -> None:
        self._result = result

    def result(self, timeout: Optional[float] = None) -> Any:
        return self._result

    def wait(self, timeout: Optional[float] = None) -> None:
        pass

    def done(self) -> bool:
        return True

    def status(self) -> str:
        return "Succeeded"


# ---------------------------------------------------------------------------
# VirtualMachineSizesOperations
# ---------------------------------------------------------------------------

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
        for vm in self._catalog.list():
            yield _vm_size_to_sdk(vm)


# ---------------------------------------------------------------------------
# VirtualMachinesOperations
# ---------------------------------------------------------------------------

class VirtualMachinesOperations:
    """Mirrors ``ComputeManagementClient.virtual_machines``.

    Create / start / stop / delete operations delegate to the
    VMInstanceManager which enforces resource constraints via cgroups.
    """

    def __init__(
        self,
        instance_manager: VMInstanceManager,
        runner: Optional[WorkloadRunner] = None,
    ) -> None:
        self._mgr = instance_manager
        self._runner = runner

    def begin_create_or_update(
        self,
        resource_group_name: str,
        vm_name: str,
        parameters: dict,
    ) -> _LROPoller:
        """Create or update a VM.

        ``parameters`` must include ``hardware_profile.vm_size`` or
        ``properties.hardwareProfile.vmSize``.
        """
        vm_size_name = self._extract_vm_size(parameters)

        existing = self._mgr.get(vm_name)
        if existing is not None:
            if existing.is_running:
                self._mgr.stop(vm_name)
            self._mgr.resize(vm_name, vm_size_name)
            vm = self._mgr.get(vm_name)
        else:
            vm = self._mgr.create(
                name=vm_name,
                vm_size_name=vm_size_name,
                resource_group=resource_group_name,
                tags=parameters.get("tags", {}),
            )
            self._mgr.start(vm_name)

        return _LROPoller(result=vm)

    def get(
        self,
        resource_group_name: str,
        vm_name: str,
        **kwargs,
    ) -> Optional[VMInstance]:
        return self._mgr.get(vm_name)

    def begin_start(
        self,
        resource_group_name: str,
        vm_name: str,
    ) -> _LROPoller:
        self._mgr.start(vm_name)
        return _LROPoller()

    def begin_deallocate(
        self,
        resource_group_name: str,
        vm_name: str,
    ) -> _LROPoller:
        self._mgr.deallocate(vm_name)
        return _LROPoller()

    def begin_power_off(
        self,
        resource_group_name: str,
        vm_name: str,
    ) -> _LROPoller:
        self._mgr.stop(vm_name)
        return _LROPoller()

    def begin_delete(
        self,
        resource_group_name: str,
        vm_name: str,
    ) -> _LROPoller:
        self._mgr.delete(vm_name)
        return _LROPoller()

    def list(
        self,
        resource_group_name: str,
        **kwargs,
    ) -> Iterator[VMInstance]:
        for vm in self._mgr.list_instances():
            if vm.resource_group == resource_group_name:
                yield vm

    def list_all(self, **kwargs) -> Iterator[VMInstance]:
        yield from self._mgr.list_instances()

    def instance_view(
        self,
        resource_group_name: str,
        vm_name: str,
    ) -> dict:
        vm = self._mgr.get(vm_name)
        if vm is None:
            raise ValueError(f"VM '{vm_name}' not found")
        return {
            "statuses": [
                {"code": vm.power_state.value, "display_status": vm.power_state.name},
                {
                    "code": f"ProvisioningState/{vm.provisioning_state.value.lower()}",
                    "display_status": vm.provisioning_state.value,
                },
            ],
        }

    @staticmethod
    def _extract_vm_size(parameters: dict) -> str:
        hp = parameters.get("hardware_profile", {})
        if isinstance(hp, dict) and "vm_size" in hp:
            return hp["vm_size"]
        props = parameters.get("properties", {})
        if isinstance(props, dict):
            hp2 = props.get("hardwareProfile", {})
            if isinstance(hp2, dict) and "vmSize" in hp2:
                return hp2["vmSize"]
        raise ValueError(
            "parameters must contain hardware_profile.vm_size or "
            "properties.hardwareProfile.vmSize"
        )


# ---------------------------------------------------------------------------
# DigitalTwinComputeManagementClient
# ---------------------------------------------------------------------------

class DigitalTwinComputeManagementClient:
    """Drop-in replacement for ``azure.mgmt.compute.ComputeManagementClient``.

    Supports two modes:

    1. **Standalone** (catalog-only) — pass ``series_filter`` and it will
       create its own VMInstanceManager.  Good for listing sizes.

    2. **Simulation** — pass a pre-configured ``instance_manager`` to get
       full VM lifecycle operations backed by cgroup enforcement.

    Example (standalone)::

        client = DigitalTwinComputeManagementClient(credential=None)
        for size in client.virtual_machine_sizes.list("eastus"):
            print(size.name)

    Example (simulation, via AzureESeriesDigitalTwin)::

        twin = AzureESeriesDigitalTwin()
        client = twin.as_compute_client()
        poller = client.virtual_machines.begin_create_or_update(
            "my-rg", "test-vm",
            {"hardware_profile": {"vm_size": "Standard_E16s_v5"}},
        )
        vm = poller.result()
    """

    def __init__(
        self,
        credential: Any = None,
        subscription_id: str = "digital-twin",
        *,
        series_filter: Optional[list[str]] = None,
        instance_manager: Optional[VMInstanceManager] = None,
        runner: Optional[WorkloadRunner] = None,
    ) -> None:
        if instance_manager is not None:
            self._manager = instance_manager
            self._catalog = instance_manager._catalog
        else:
            self._catalog = ESeriesCatalog(series_filter=series_filter)
            self._manager = VMInstanceManager(catalog=self._catalog)

        self._runner = runner
        self.subscription_id = subscription_id

        self.virtual_machine_sizes = VirtualMachineSizesOperations(self._catalog)
        self.virtual_machines = VirtualMachinesOperations(
            self._manager, self._runner
        )

    @property
    def catalog(self) -> ESeriesCatalog:
        return self._catalog

    def close(self) -> None:
        self._manager.cleanup()

    def __enter__(self) -> "DigitalTwinComputeManagementClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
