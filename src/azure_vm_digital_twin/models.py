"""Data models for the Azure E-Series VM digital twin.

These models mirror the structure of azure-mgmt-compute SDK types
(VirtualMachineSize, HardwareProfile, StorageProfile, etc.) to ensure
API-level compatibility when used alongside the real Azure SDK.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class CompatibilityStatus(enum.Enum):
    """Overall compatibility verdict."""

    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_WARNINGS = "compatible_with_warnings"
    INCOMPATIBLE = "incompatible"


class ProcessorArchitecture(enum.Enum):
    """Processor architecture."""

    X86_64 = "x86-64"
    ARM64 = "ARM-64"


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
    detail fields used by the digital-twin compatibility engine.
    """

    name: str
    number_of_cores: int
    memory_in_mb: int
    series: str
    processor: str
    architecture: ProcessorArchitecture
    storage: StorageCapability
    network: NetworkCapability

    # azure-mgmt-compute compatible property names
    @property
    def os_disk_size_in_mb(self) -> int:
        return self.storage.os_disk_size_in_gb * 1024

    @property
    def resource_disk_size_in_mb(self) -> int:
        return self.storage.temp_disk_size_gb * 1024

    @property
    def max_data_disk_count(self) -> int:
        return self.storage.max_data_disk_count

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


@dataclass
class OnPremVMProfile:
    """Captured profile of an on-premises virtual machine."""

    hostname: str
    vcpus: int
    memory_mb: int
    os_type: str  # "Linux" | "Windows"
    architecture: ProcessorArchitecture = ProcessorArchitecture.X86_64
    data_disks_count: int = 0
    total_disk_size_gb: int = 0
    required_iops: int = 0
    required_throughput_mbps: int = 0
    required_nics: int = 1
    required_bandwidth_mbps: int = 0
    requires_temp_disk: bool = False
    requires_premium_io: bool = False
    requires_ultra_ssd: bool = False
    requires_accelerated_networking: bool = False
    gpu_required: bool = False
    custom_labels: dict = field(default_factory=dict)


@dataclass
class CompatibilityDetail:
    """A single compatibility check result."""

    dimension: str
    required: str
    available: str
    passed: bool
    message: str = ""


@dataclass
class CompatibilityResult:
    """Result of comparing an on-prem VM against an Azure E-series VM size."""

    vm_size: VMSize
    on_prem: OnPremVMProfile
    status: CompatibilityStatus
    details: list[CompatibilityDetail] = field(default_factory=list)
    overall_message: str = ""

    @property
    def is_compatible(self) -> bool:
        return self.status in (
            CompatibilityStatus.COMPATIBLE,
            CompatibilityStatus.COMPATIBLE_WITH_WARNINGS,
        )

    def summary(self) -> str:
        lines = [
            f"VM Size: {self.vm_size.name}",
            f"Status:  {self.status.value}",
            f"Message: {self.overall_message}",
            "",
            "Details:",
        ]
        for d in self.details:
            icon = "PASS" if d.passed else "FAIL"
            lines.append(f"  [{icon}] {d.dimension}: need {d.required}, have {d.available}")
            if d.message:
                lines.append(f"         {d.message}")
        return "\n".join(lines)


@dataclass
class MigrationRecommendation:
    """Ranked recommendation of E-series VM sizes for a given on-prem VM."""

    on_prem: OnPremVMProfile
    compatible_sizes: list[CompatibilityResult] = field(default_factory=list)
    best_fit: Optional[CompatibilityResult] = None
    incompatible_sizes: list[CompatibilityResult] = field(default_factory=list)
