"""Collect on-premises VM hardware profile for migration compatibility testing.

Uses ``psutil`` for live host introspection, with a manual-entry fallback
for environments where psutil is unavailable or when profiling a remote host.
"""

from __future__ import annotations

import platform
import socket
from typing import Optional

from azure_vm_digital_twin.models import OnPremVMProfile, ProcessorArchitecture


def _detect_architecture() -> ProcessorArchitecture:
    machine = platform.machine().lower()
    if machine in ("aarch64", "arm64"):
        return ProcessorArchitecture.ARM64
    return ProcessorArchitecture.X86_64


def collect_local_profile(
    override_hostname: Optional[str] = None,
    data_disks_count: int = 0,
    total_disk_size_gb: int = 0,
    required_iops: int = 0,
    required_throughput_mbps: int = 0,
    required_nics: int = 1,
    required_bandwidth_mbps: int = 0,
    requires_temp_disk: bool = False,
    requires_premium_io: bool = False,
    requires_ultra_ssd: bool = False,
    requires_accelerated_networking: bool = False,
) -> OnPremVMProfile:
    """Build a profile by introspecting the current host via ``psutil``.

    Storage and network *requirements* must be provided manually since they
    represent the workload's needs rather than installed hardware.
    """
    import psutil

    os_type = "Windows" if platform.system() == "Windows" else "Linux"
    hostname = override_hostname or socket.gethostname()
    vcpus = psutil.cpu_count(logical=True) or 1
    memory_mb = int(psutil.virtual_memory().total / (1024 * 1024))

    return OnPremVMProfile(
        hostname=hostname,
        vcpus=vcpus,
        memory_mb=memory_mb,
        os_type=os_type,
        architecture=_detect_architecture(),
        data_disks_count=data_disks_count,
        total_disk_size_gb=total_disk_size_gb,
        required_iops=required_iops,
        required_throughput_mbps=required_throughput_mbps,
        required_nics=required_nics,
        required_bandwidth_mbps=required_bandwidth_mbps,
        requires_temp_disk=requires_temp_disk,
        requires_premium_io=requires_premium_io,
        requires_ultra_ssd=requires_ultra_ssd,
        requires_accelerated_networking=requires_accelerated_networking,
    )


def create_manual_profile(
    hostname: str,
    vcpus: int,
    memory_mb: int,
    os_type: str = "Linux",
    architecture: ProcessorArchitecture = ProcessorArchitecture.X86_64,
    data_disks_count: int = 0,
    total_disk_size_gb: int = 0,
    required_iops: int = 0,
    required_throughput_mbps: int = 0,
    required_nics: int = 1,
    required_bandwidth_mbps: int = 0,
    requires_temp_disk: bool = False,
    requires_premium_io: bool = False,
    requires_ultra_ssd: bool = False,
    requires_accelerated_networking: bool = False,
    gpu_required: bool = False,
) -> OnPremVMProfile:
    """Build a profile from manually specified values."""
    return OnPremVMProfile(
        hostname=hostname,
        vcpus=vcpus,
        memory_mb=memory_mb,
        os_type=os_type,
        architecture=architecture,
        data_disks_count=data_disks_count,
        total_disk_size_gb=total_disk_size_gb,
        required_iops=required_iops,
        required_throughput_mbps=required_throughput_mbps,
        required_nics=required_nics,
        required_bandwidth_mbps=required_bandwidth_mbps,
        requires_temp_disk=requires_temp_disk,
        requires_premium_io=requires_premium_io,
        requires_ultra_ssd=requires_ultra_ssd,
        requires_accelerated_networking=requires_accelerated_networking,
        gpu_required=gpu_required,
    )
