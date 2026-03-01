"""VM instance lifecycle manager.

Creates, starts, stops, and destroys digital-twin VM instances backed
by cgroup sandboxes that enforce the E-series SKU's resource limits.
"""

from __future__ import annotations

import logging
from typing import Optional

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import (
    ProvisioningState,
    VMInstance,
    VMPowerState,
    VMSize,
)
from azure_vm_digital_twin.simulator.network_governor import NetworkGovernor
from azure_vm_digital_twin.simulator.resource_governor import (
    AppliedConstraints,
    ResourceGovernor,
)

logger = logging.getLogger(__name__)


class VMInstanceManager:
    """Manages the full lifecycle of digital-twin VM instances.

    Each VM instance maps to a cgroup sandbox that enforces the
    CPU / memory / IO / network limits of the chosen E-series SKU.

    Usage::

        mgr = VMInstanceManager()
        vm = mgr.create("test-vm", "Standard_E8s_v5")
        mgr.start("test-vm")
        # ... run workloads via WorkloadRunner ...
        mgr.stop("test-vm")
        mgr.delete("test-vm")
    """

    def __init__(
        self,
        catalog: Optional[ESeriesCatalog] = None,
        network_interface: str = "eth0",
    ) -> None:
        self._catalog = catalog or ESeriesCatalog()
        self._governor = ResourceGovernor()
        self._net_governor = NetworkGovernor(interface=network_interface)
        self._instances: dict[str, VMInstance] = {}

    @property
    def governor(self) -> ResourceGovernor:
        return self._governor

    @property
    def net_governor(self) -> NetworkGovernor:
        return self._net_governor

    def list_instances(self) -> list[VMInstance]:
        return list(self._instances.values())

    def get(self, name: str) -> Optional[VMInstance]:
        return self._instances.get(name)

    def create(
        self,
        name: str,
        vm_size_name: str,
        location: str = "digital-twin",
        resource_group: str = "digital-twin-rg",
        tags: Optional[dict] = None,
    ) -> VMInstance:
        """Create a digital-twin VM instance.

        Resolves the SKU from the catalog, creates the VM record, but does
        NOT yet enforce resource limits (call ``start()`` for that).
        """
        if name in self._instances:
            raise ValueError(f"VM '{name}' already exists")

        vm_size = self._catalog.get_by_name(vm_size_name)
        if vm_size is None:
            available = [s.name for s in self._catalog.list()]
            raise ValueError(
                f"Unknown VM size '{vm_size_name}'. "
                f"Available: {available[:5]}..."
            )

        vm = VMInstance(
            name=name,
            vm_size=vm_size,
            location=location,
            resource_group=resource_group,
            power_state=VMPowerState.STOPPED,
            provisioning_state=ProvisioningState.SUCCEEDED,
            tags=tags or {},
        )
        self._instances[name] = vm
        logger.info("Created VM '%s' with size %s", name, vm_size_name)
        return vm

    def start(self, name: str) -> AppliedConstraints:
        """Start a VM — creates the cgroup sandbox and enforces limits.

        After this call, workloads run via ``WorkloadRunner`` will be
        constrained to the SKU's resource envelope.
        """
        vm = self._require_instance(name)
        if vm.is_running:
            return self._governor.get_constraints(name)

        vm.power_state = VMPowerState.STARTING
        vm.provisioning_state = ProvisioningState.UPDATING

        constraints = self._governor.create_sandbox(
            name=name,
            cpu_cores=vm.vm_size.number_of_cores,
            memory_mb=vm.vm_size.memory_in_mb,
            iops_limit=vm.vm_size.storage.max_iops,
            throughput_mbps=vm.vm_size.storage.max_throughput_mbps,
            net_bandwidth_mbps=vm.vm_size.network.expected_bandwidth_mbps,
        )
        vm.cgroup_path = constraints.cgroup_path or ""

        # Network shaping
        if vm.vm_size.network.expected_bandwidth_mbps:
            self._net_governor.apply_limit(
                name, vm.vm_size.network.expected_bandwidth_mbps
            )

        vm.power_state = VMPowerState.RUNNING
        vm.provisioning_state = ProvisioningState.SUCCEEDED
        logger.info(
            "Started VM '%s': %d vCPUs, %d MB RAM, enforcement=%s",
            name, vm.vm_size.number_of_cores, vm.vm_size.memory_in_mb,
            constraints.method,
        )
        return constraints

    def stop(self, name: str) -> None:
        """Stop a VM — releases cgroup constraints but keeps the instance."""
        vm = self._require_instance(name)
        vm.power_state = VMPowerState.STOPPING

        self._governor.destroy_sandbox(name)
        self._net_governor.remove_limit(name)

        vm.power_state = VMPowerState.STOPPED
        vm.cgroup_path = ""
        logger.info("Stopped VM '%s'", name)

    def deallocate(self, name: str) -> None:
        """Deallocate a VM — same as stop for digital twin."""
        vm = self._require_instance(name)
        if vm.is_running:
            self.stop(name)
        vm.power_state = VMPowerState.DEALLOCATED

    def delete(self, name: str) -> None:
        """Delete a VM instance entirely."""
        vm = self._instances.get(name)
        if vm is None:
            return
        if vm.is_running:
            self.stop(name)
        vm.provisioning_state = ProvisioningState.DELETING
        self._instances.pop(name, None)
        logger.info("Deleted VM '%s'", name)

    def resize(self, name: str, new_size_name: str) -> VMInstance:
        """Resize a VM to a different E-series SKU.

        The VM must be stopped before resizing (matches Azure behavior).
        """
        vm = self._require_instance(name)
        if vm.is_running:
            raise RuntimeError("VM must be stopped before resizing")

        new_size = self._catalog.get_by_name(new_size_name)
        if new_size is None:
            raise ValueError(f"Unknown VM size '{new_size_name}'")

        vm.vm_size = new_size
        vm.provisioning_state = ProvisioningState.SUCCEEDED
        logger.info("Resized VM '%s' to %s", name, new_size_name)
        return vm

    def cleanup(self) -> None:
        """Destroy all sandboxes and clean up resources."""
        for name in list(self._instances):
            self.delete(name)
        self._governor.destroy_all()
        self._net_governor.remove_all()

    def _require_instance(self, name: str) -> VMInstance:
        vm = self._instances.get(name)
        if vm is None:
            raise ValueError(f"VM '{name}' does not exist")
        return vm
