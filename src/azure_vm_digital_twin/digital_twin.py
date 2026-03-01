"""Azure E-Series Digital Twin — simulation orchestrator.

This is the top-level entry point.  It wires together the VM catalog,
the cgroup-based resource governor, and the workload runner so that
callers can:

1. Create a digital-twin VM pinned to an E-series SKU.
2. Start it (enforce CPU / memory / IO / network limits).
3. Run real workloads inside those limits and collect metrics.
4. Inspect whether the workload survived, was throttled, or OOM-killed.
5. Stop / resize / delete the VM.

The class also exposes an ``as_compute_client()`` helper that returns an
azure-mgmt-compute-compatible client for SDK interoperability.
"""

from __future__ import annotations

import logging
from typing import Optional

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import (
    VMInstance,
    VMSize,
    WorkloadResult,
)
from azure_vm_digital_twin.simulator.resource_governor import AppliedConstraints
from azure_vm_digital_twin.simulator.vm_instance import VMInstanceManager
from azure_vm_digital_twin.workload.runner import WorkloadRunner

logger = logging.getLogger(__name__)


class AzureESeriesDigitalTwin:
    """Top-level facade for E-series digital-twin simulation.

    Example::

        twin = AzureESeriesDigitalTwin()

        # Create and start a VM pinned to Standard_E8s_v5 constraints
        twin.create_vm("web-test", "Standard_E8s_v5")
        twin.start_vm("web-test")

        # Run a real workload under those constraints
        result = twin.run_workload("web-test", ["stress-ng", "--cpu", "8", "-t", "10"])
        print(result.summary())

        # Check if the workload would survive on this SKU
        if result.passed:
            print("Workload is viable on Standard_E8s_v5")
        else:
            print("Workload exceeded resource limits!")

        twin.stop_vm("web-test")

        # SDK-compatible client
        client = twin.as_compute_client()
        for vm in client.virtual_machines.list("digital-twin-rg"):
            print(vm.name, vm.vm_size.name)
    """

    def __init__(
        self,
        series_filter: Optional[list[str]] = None,
        sample_interval: float = 0.5,
        network_interface: str = "eth0",
    ) -> None:
        self._catalog = ESeriesCatalog(series_filter=series_filter)
        self._manager = VMInstanceManager(
            catalog=self._catalog,
            network_interface=network_interface,
        )
        self._runner = WorkloadRunner(
            instance_manager=self._manager,
            sample_interval=sample_interval,
        )

    # -- Properties ---------------------------------------------------------

    @property
    def catalog(self) -> ESeriesCatalog:
        return self._catalog

    @property
    def manager(self) -> VMInstanceManager:
        return self._manager

    @property
    def runner(self) -> WorkloadRunner:
        return self._runner

    # -- VM lifecycle -------------------------------------------------------

    def create_vm(
        self,
        name: str,
        vm_size_name: str,
        location: str = "digital-twin",
        resource_group: str = "digital-twin-rg",
        tags: Optional[dict] = None,
    ) -> VMInstance:
        """Create a digital-twin VM bound to an E-series SKU."""
        return self._manager.create(
            name=name,
            vm_size_name=vm_size_name,
            location=location,
            resource_group=resource_group,
            tags=tags,
        )

    def start_vm(self, name: str) -> AppliedConstraints:
        """Start a VM — enforces SKU resource constraints via cgroups."""
        return self._manager.start(name)

    def stop_vm(self, name: str) -> None:
        """Stop a VM — releases resource constraints."""
        self._manager.stop(name)

    def deallocate_vm(self, name: str) -> None:
        """Deallocate a VM."""
        self._manager.deallocate(name)

    def delete_vm(self, name: str) -> None:
        """Delete a VM instance."""
        self._manager.delete(name)

    def resize_vm(self, name: str, new_size_name: str) -> VMInstance:
        """Resize a stopped VM to a different E-series SKU."""
        return self._manager.resize(name, new_size_name)

    def get_vm(self, name: str) -> Optional[VMInstance]:
        """Get a VM instance by name."""
        return self._manager.get(name)

    def list_vms(self) -> list[VMInstance]:
        """List all digital-twin VM instances."""
        return self._manager.list_instances()

    # -- Workload execution -------------------------------------------------

    def run_workload(
        self,
        vm_name: str,
        command: list[str],
        timeout: Optional[float] = None,
        env: Optional[dict] = None,
        cwd: Optional[str] = None,
    ) -> WorkloadResult:
        """Run a workload command inside a VM's resource sandbox.

        The command runs as a real process constrained to the VM's SKU
        limits (CPU cores, memory, IOPS, network bandwidth).  Metrics
        are collected throughout and returned in the result.
        """
        return self._runner.run(
            vm_name=vm_name,
            command=command,
            timeout=timeout,
            env=env,
            cwd=cwd,
        )

    def run_script(
        self,
        vm_name: str,
        script: str,
        interpreter: str = "bash",
        timeout: Optional[float] = None,
    ) -> WorkloadResult:
        """Run a shell script inside a VM's resource sandbox."""
        return self._runner.run_script(
            vm_name=vm_name,
            script=script,
            interpreter=interpreter,
            timeout=timeout,
        )

    # -- Reporting ----------------------------------------------------------

    def generate_report(self, vm_name: str) -> str:
        """Generate a report of all workload runs for a VM."""
        vm = self._manager.get(vm_name)
        if vm is None:
            return f"VM '{vm_name}' not found."

        lines = [
            "=" * 72,
            "Azure E-Series Digital Twin — Workload Simulation Report",
            "=" * 72,
            "",
            f"VM Name:       {vm.name}",
            f"VM Size:       {vm.vm_size.name}  ({vm.vm_size.series})",
            f"  vCPUs:       {vm.vm_size.number_of_cores}",
            f"  Memory:      {vm.vm_size.memory_in_mb} MB"
            f" ({vm.vm_size.memory_in_mb // 1024} GB)",
            f"  Max IOPS:    {vm.vm_size.storage.max_iops}",
            f"  Bandwidth:   {vm.vm_size.network.expected_bandwidth_mbps} Mbps",
            f"  Power state: {vm.power_state.value}",
            f"  Enforcement: {self._manager.governor.enforcement_method}",
            "",
        ]

        if not vm.workload_results:
            lines.append("No workloads have been run yet.")
        else:
            passed = sum(1 for r in vm.workload_results if r.passed)
            failed = len(vm.workload_results) - passed
            lines += [
                f"Workloads run: {len(vm.workload_results)}  "
                f"(passed={passed}, failed={failed})",
                "",
            ]
            for i, r in enumerate(vm.workload_results, 1):
                lines += [
                    "-" * 72,
                    f"Workload #{i}",
                    "-" * 72,
                    r.summary(),
                    "",
                ]

        lines.append("=" * 72)
        return "\n".join(lines)

    # -- SDK compat ---------------------------------------------------------

    def as_compute_client(self):
        """Return an azure-mgmt-compute-compatible client.

        Supports both ``virtual_machine_sizes.list(location)`` and
        ``virtual_machines`` operations (list, get, create, start, stop).
        """
        from azure_vm_digital_twin.sdk_compat import (
            DigitalTwinComputeManagementClient,
        )
        return DigitalTwinComputeManagementClient(
            instance_manager=self._manager,
            runner=self._runner,
        )

    # -- Cleanup ------------------------------------------------------------

    def cleanup(self) -> None:
        """Destroy all VMs and release all resources."""
        self._manager.cleanup()
