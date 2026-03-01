"""Data models for the Azure E-Series VM digital twin.

These models mirror the structure of azure-mgmt-compute SDK types
(VirtualMachineSize, HardwareProfile, StorageProfile, etc.) to ensure
API-level compatibility when used alongside the real Azure SDK.

The simulation models (VMInstance, SimulationMetrics, WorkloadResult)
represent the runtime state of a digital-twin VM that enforces real
resource constraints via Linux cgroups so customer workloads can be
tested against E-series specifications.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProcessorArchitecture(enum.Enum):
    X86_64 = "x86-64"
    ARM64 = "ARM-64"


class VMPowerState(enum.Enum):
    """Mirrors azure.mgmt.compute InstanceViewStatus power states."""
    CREATING = "PowerState/creating"
    STARTING = "PowerState/starting"
    RUNNING = "PowerState/running"
    STOPPING = "PowerState/stopping"
    STOPPED = "PowerState/stopped"
    DEALLOCATING = "PowerState/deallocating"
    DEALLOCATED = "PowerState/deallocated"


class ProvisioningState(enum.Enum):
    CREATING = "Creating"
    UPDATING = "Updating"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    DELETING = "Deleting"


# ---------------------------------------------------------------------------
# VM Size specifications (kept from original)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StorageCapability:
    """Storage characteristics for a VM size."""
    max_data_disk_count: int
    os_disk_size_in_gb: int = 1024
    max_iops: int = 0
    max_throughput_mbps: int = 0
    has_temp_disk: bool = False
    temp_disk_size_gb: int = 0
    temp_disk_iops: int = 0
    temp_disk_throughput_mbps: int = 0
    premium_io_supported: bool = True
    ultra_ssd_supported: bool = False


@dataclass(frozen=True)
class NetworkCapability:
    """Network characteristics for a VM size."""
    max_nics: int
    expected_bandwidth_mbps: int
    accelerated_networking: bool = True


@dataclass(frozen=True)
class VMSize:
    """Represents an Azure VM size with full specifications.

    Mirrors ``azure.mgmt.compute.models.VirtualMachineSize`` with additional
    detail fields used by the digital-twin simulation engine.
    """
    name: str
    number_of_cores: int
    memory_in_mb: int
    series: str
    processor: str
    architecture: ProcessorArchitecture
    storage: StorageCapability
    network: NetworkCapability

    @property
    def os_disk_size_in_mb(self) -> int:
        return self.storage.os_disk_size_in_gb * 1024

    @property
    def resource_disk_size_in_mb(self) -> int:
        return self.storage.temp_disk_size_gb * 1024

    @property
    def max_data_disk_count(self) -> int:
        return self.storage.max_data_disk_count

    @property
    def memory_in_bytes(self) -> int:
        return self.memory_in_mb * 1024 * 1024

    def as_sdk_dict(self) -> dict:
        """Return a dictionary matching the azure-mgmt-compute VirtualMachineSize shape."""
        return {
            "name": self.name,
            "number_of_cores": self.number_of_cores,
            "memory_in_mb": self.memory_in_mb,
            "os_disk_size_in_mb": self.os_disk_size_in_mb,
            "resource_disk_size_in_mb": self.resource_disk_size_in_mb,
            "max_data_disk_count": self.max_data_disk_count,
        }


# ---------------------------------------------------------------------------
# Simulation runtime models
# ---------------------------------------------------------------------------

@dataclass
class ResourceSnapshot:
    """Point-in-time resource usage captured during simulation."""
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    io_read_ops: int = 0
    io_write_ops: int = 0
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    cpu_throttled_periods: int = 0
    cpu_throttled_time_us: int = 0
    memory_oom_events: int = 0


@dataclass
class SimulationMetrics:
    """Aggregated metrics from a workload simulation run."""
    vm_size_name: str = ""
    duration_seconds: float = 0.0
    exit_code: int = 0

    # CPU
    peak_cpu_percent: float = 0.0
    avg_cpu_percent: float = 0.0
    cpu_throttled_periods: int = 0
    cpu_throttled_time_seconds: float = 0.0

    # Memory
    peak_memory_mb: float = 0.0
    peak_memory_percent: float = 0.0
    avg_memory_mb: float = 0.0
    oom_kill_count: int = 0

    # I/O
    total_read_bytes: int = 0
    total_write_bytes: int = 0
    total_read_ops: int = 0
    total_write_ops: int = 0
    avg_iops: float = 0.0
    peak_iops: float = 0.0

    # Network
    total_net_sent_bytes: int = 0
    total_net_recv_bytes: int = 0

    # Snapshots for time-series analysis
    snapshots: list[ResourceSnapshot] = field(default_factory=list)

    @property
    def was_cpu_constrained(self) -> bool:
        return self.cpu_throttled_periods > 0

    @property
    def was_memory_constrained(self) -> bool:
        return self.oom_kill_count > 0 or self.peak_memory_percent > 90.0

    @property
    def workload_succeeded(self) -> bool:
        return self.exit_code == 0 and self.oom_kill_count == 0


@dataclass
class WorkloadResult:
    """Complete result of running a workload inside a digital-twin VM."""
    vm_instance_name: str
    vm_size: VMSize
    command: list[str]
    metrics: SimulationMetrics
    stdout: str = ""
    stderr: str = ""
    enforced_constraints: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.metrics.workload_succeeded

    def summary(self) -> str:
        m = self.metrics
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"Workload Simulation Result: {status}",
            f"  VM Size:        {self.vm_size.name}",
            f"  Command:        {' '.join(self.command)}",
            f"  Duration:       {m.duration_seconds:.2f}s",
            f"  Exit code:      {m.exit_code}",
            "",
            "  CPU:",
            f"    Peak:         {m.peak_cpu_percent:.1f}%",
            f"    Average:      {m.avg_cpu_percent:.1f}%",
            f"    Throttled:    {m.cpu_throttled_periods} periods"
            f" ({m.cpu_throttled_time_seconds:.3f}s)",
            "",
            "  Memory:",
            f"    Limit:        {self.vm_size.memory_in_mb} MB",
            f"    Peak:         {m.peak_memory_mb:.1f} MB"
            f" ({m.peak_memory_percent:.1f}%)",
            f"    OOM kills:    {m.oom_kill_count}",
            "",
            "  I/O:",
            f"    Read:         {m.total_read_bytes} bytes"
            f" ({m.total_read_ops} ops)",
            f"    Write:        {m.total_write_bytes} bytes"
            f" ({m.total_write_ops} ops)",
            f"    Avg IOPS:     {m.avg_iops:.1f}",
        ]
        if self.enforced_constraints:
            lines += ["", "  Enforced constraints:"]
            for k, v in self.enforced_constraints.items():
                lines.append(f"    {k}: {v}")
        return "\n".join(lines)


@dataclass
class VMInstance:
    """Runtime state of a simulated E-series VM.

    Mirrors azure.mgmt.compute.models.VirtualMachine fields that matter
    for the simulation: name, location, vm_size, power state, and the
    cgroup path used to enforce constraints.
    """
    name: str
    vm_size: VMSize
    location: str = "digital-twin"
    resource_group: str = "digital-twin-rg"
    power_state: VMPowerState = VMPowerState.DEALLOCATED
    provisioning_state: ProvisioningState = ProvisioningState.SUCCEEDED
    cgroup_path: str = ""
    created_at: float = field(default_factory=time.time)
    workload_results: list[WorkloadResult] = field(default_factory=list)
    tags: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return (
            f"/subscriptions/digital-twin/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.Compute/virtualMachines/{self.name}"
        )

    @property
    def is_running(self) -> bool:
        return self.power_state == VMPowerState.RUNNING

    def as_sdk_dict(self) -> dict:
        """Return a dict matching azure.mgmt.compute.models.VirtualMachine shape."""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "tags": self.tags,
            "properties": {
                "hardwareProfile": {"vmSize": self.vm_size.name},
                "provisioningState": self.provisioning_state.value,
                "instanceView": {
                    "statuses": [
                        {"code": self.power_state.value},
                        {"code": f"ProvisioningState/{self.provisioning_state.value.lower()}"},
                    ]
                },
            },
        }
