"""Compatibility analysis engine.

Compares an on-premises VM profile against each E-series VM size across
every relevant dimension (vCPUs, memory, storage, network, architecture)
and produces ranked migration recommendations.
"""

from __future__ import annotations

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import (
    CompatibilityDetail,
    CompatibilityResult,
    CompatibilityStatus,
    MigrationRecommendation,
    OnPremVMProfile,
    VMSize,
)


def _check_vcpus(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    passed = vm.number_of_cores >= on_prem.vcpus
    return CompatibilityDetail(
        dimension="vCPUs",
        required=str(on_prem.vcpus),
        available=str(vm.number_of_cores),
        passed=passed,
        message="" if passed else "Insufficient vCPU count",
    )


def _check_memory(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    passed = vm.memory_in_mb >= on_prem.memory_mb
    return CompatibilityDetail(
        dimension="Memory (MB)",
        required=str(on_prem.memory_mb),
        available=str(vm.memory_in_mb),
        passed=passed,
        message="" if passed else "Insufficient memory",
    )


def _check_data_disks(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    passed = vm.storage.max_data_disk_count >= on_prem.data_disks_count
    return CompatibilityDetail(
        dimension="Data disks",
        required=str(on_prem.data_disks_count),
        available=str(vm.storage.max_data_disk_count),
        passed=passed,
        message="" if passed else "Not enough data disk slots",
    )


def _check_iops(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if on_prem.required_iops == 0:
        return CompatibilityDetail(
            dimension="IOPS",
            required="none specified",
            available=str(vm.storage.max_iops),
            passed=True,
        )
    passed = vm.storage.max_iops >= on_prem.required_iops
    return CompatibilityDetail(
        dimension="IOPS",
        required=str(on_prem.required_iops),
        available=str(vm.storage.max_iops),
        passed=passed,
        message="" if passed else "IOPS requirement not met",
    )


def _check_throughput(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if on_prem.required_throughput_mbps == 0:
        return CompatibilityDetail(
            dimension="Storage throughput (MBps)",
            required="none specified",
            available=str(vm.storage.max_throughput_mbps),
            passed=True,
        )
    passed = vm.storage.max_throughput_mbps >= on_prem.required_throughput_mbps
    return CompatibilityDetail(
        dimension="Storage throughput (MBps)",
        required=str(on_prem.required_throughput_mbps),
        available=str(vm.storage.max_throughput_mbps),
        passed=passed,
        message="" if passed else "Storage throughput requirement not met",
    )


def _check_nics(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    passed = vm.network.max_nics >= on_prem.required_nics
    return CompatibilityDetail(
        dimension="NICs",
        required=str(on_prem.required_nics),
        available=str(vm.network.max_nics),
        passed=passed,
        message="" if passed else "Not enough network interfaces",
    )


def _check_bandwidth(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if on_prem.required_bandwidth_mbps == 0:
        return CompatibilityDetail(
            dimension="Network bandwidth (Mbps)",
            required="none specified",
            available=str(vm.network.expected_bandwidth_mbps),
            passed=True,
        )
    passed = vm.network.expected_bandwidth_mbps >= on_prem.required_bandwidth_mbps
    return CompatibilityDetail(
        dimension="Network bandwidth (Mbps)",
        required=str(on_prem.required_bandwidth_mbps),
        available=str(vm.network.expected_bandwidth_mbps),
        passed=passed,
        message="" if passed else "Network bandwidth requirement not met",
    )


def _check_temp_disk(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if not on_prem.requires_temp_disk:
        return CompatibilityDetail(
            dimension="Temp disk",
            required="not required",
            available="yes" if vm.storage.has_temp_disk else "no",
            passed=True,
        )
    passed = vm.storage.has_temp_disk
    return CompatibilityDetail(
        dimension="Temp disk",
        required="required",
        available="yes" if passed else "no",
        passed=passed,
        message="" if passed else "Workload requires temp disk but VM size has none",
    )


def _check_premium_io(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if not on_prem.requires_premium_io:
        return CompatibilityDetail(
            dimension="Premium IO",
            required="not required",
            available="yes" if vm.storage.premium_io_supported else "no",
            passed=True,
        )
    passed = vm.storage.premium_io_supported
    return CompatibilityDetail(
        dimension="Premium IO",
        required="required",
        available="yes" if passed else "no",
        passed=passed,
        message="" if passed else "Premium IO not supported",
    )


def _check_ultra_ssd(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if not on_prem.requires_ultra_ssd:
        return CompatibilityDetail(
            dimension="Ultra SSD",
            required="not required",
            available="yes" if vm.storage.ultra_ssd_supported else "no",
            passed=True,
        )
    passed = vm.storage.ultra_ssd_supported
    return CompatibilityDetail(
        dimension="Ultra SSD",
        required="required",
        available="yes" if passed else "no",
        passed=passed,
        message="" if passed else "Ultra SSD not supported on this size",
    )


def _check_architecture(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    passed = vm.architecture == on_prem.architecture
    return CompatibilityDetail(
        dimension="Architecture",
        required=on_prem.architecture.value,
        available=vm.architecture.value,
        passed=passed,
        message="" if passed else "Architecture mismatch (may require recompilation)",
    )


def _check_gpu(on_prem: OnPremVMProfile, vm: VMSize) -> CompatibilityDetail:
    if not on_prem.gpu_required:
        return CompatibilityDetail(
            dimension="GPU",
            required="not required",
            available="none (E-series is CPU-only)",
            passed=True,
        )
    return CompatibilityDetail(
        dimension="GPU",
        required="required",
        available="none (E-series is CPU-only)",
        passed=False,
        message="E-series VMs do not have GPUs; consider N-series instead",
    )


_ALL_CHECKS = [
    _check_vcpus,
    _check_memory,
    _check_data_disks,
    _check_iops,
    _check_throughput,
    _check_nics,
    _check_bandwidth,
    _check_temp_disk,
    _check_premium_io,
    _check_ultra_ssd,
    _check_architecture,
    _check_gpu,
]


def evaluate_compatibility(
    on_prem: OnPremVMProfile, vm: VMSize
) -> CompatibilityResult:
    """Run all compatibility checks for a single VM size."""
    details = [check(on_prem, vm) for check in _ALL_CHECKS]
    failures = [d for d in details if not d.passed]

    if not failures:
        status = CompatibilityStatus.COMPATIBLE
        msg = f"{vm.name} fully meets all requirements"
    elif all(d.dimension == "Architecture" for d in failures):
        status = CompatibilityStatus.COMPATIBLE_WITH_WARNINGS
        msg = f"{vm.name} compatible but architecture differs"
    else:
        status = CompatibilityStatus.INCOMPATIBLE
        dims = ", ".join(d.dimension for d in failures)
        msg = f"{vm.name} incompatible: {dims}"

    return CompatibilityResult(
        vm_size=vm,
        on_prem=on_prem,
        status=status,
        details=details,
        overall_message=msg,
    )


def recommend_sizes(
    on_prem: OnPremVMProfile,
    catalog: Optional[ESeriesCatalog] = None,
) -> MigrationRecommendation:
    """Evaluate all E-series sizes and return a ranked recommendation.

    Compatible sizes are ranked by *closeness of fit* (smallest size that
    still satisfies all requirements) to minimize cost.
    """
    if catalog is None:
        catalog = ESeriesCatalog()

    compatible: list[CompatibilityResult] = []
    incompatible: list[CompatibilityResult] = []

    for vm in catalog.list():
        result = evaluate_compatibility(on_prem, vm)
        if result.is_compatible:
            compatible.append(result)
        else:
            incompatible.append(result)

    # Rank compatible sizes: prefer smallest memory that still fits
    compatible.sort(key=lambda r: (r.vm_size.memory_in_mb, r.vm_size.number_of_cores))

    best = compatible[0] if compatible else None

    return MigrationRecommendation(
        on_prem=on_prem,
        compatible_sizes=compatible,
        best_fit=best,
        incompatible_sizes=incompatible,
    )


# Allow `from ... import Optional` to resolve at module level
from typing import Optional  # noqa: E402  (used in recommend_sizes signature)
