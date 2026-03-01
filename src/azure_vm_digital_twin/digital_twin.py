"""High-level orchestrator for the Azure E-Series digital twin.

Provides a single entry point that collects an on-prem profile, runs the
compatibility analysis, and returns actionable migration recommendations.
"""

from __future__ import annotations

from typing import Optional

from azure_vm_digital_twin.compatibility_analyzer import (
    evaluate_compatibility,
    recommend_sizes,
)
from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import (
    CompatibilityResult,
    MigrationRecommendation,
    OnPremVMProfile,
    ProcessorArchitecture,
    VMSize,
)
from azure_vm_digital_twin.on_prem_collector import (
    collect_local_profile,
    create_manual_profile,
)
from azure_vm_digital_twin.sdk_compat import DigitalTwinComputeManagementClient


class AzureESeriesDigitalTwin:
    """Top-level facade for E-series digital twin validation.

    Example::

        twin = AzureESeriesDigitalTwin()

        # From manual specs
        profile = twin.profile_from_specs(
            hostname="db-server-01",
            vcpus=16,
            memory_mb=131072,
            data_disks_count=8,
            required_iops=25000,
        )
        rec = twin.recommend(profile)
        print(rec.best_fit.summary())

        # SDK-compatible client
        client = twin.as_compute_client()
        for size in client.virtual_machine_sizes.list("eastus"):
            print(size.name, size.memory_in_mb)
    """

    def __init__(self, series_filter: Optional[list[str]] = None) -> None:
        self._catalog = ESeriesCatalog(series_filter=series_filter)

    @property
    def catalog(self) -> ESeriesCatalog:
        return self._catalog

    # -- Profile creation ---------------------------------------------------

    def profile_from_local(self, **kwargs) -> OnPremVMProfile:
        """Auto-detect the current host's hardware profile."""
        return collect_local_profile(**kwargs)

    def profile_from_specs(
        self,
        hostname: str = "on-prem-vm",
        vcpus: int = 1,
        memory_mb: int = 1024,
        os_type: str = "Linux",
        architecture: ProcessorArchitecture = ProcessorArchitecture.X86_64,
        **kwargs,
    ) -> OnPremVMProfile:
        """Build a profile from manually specified values."""
        return create_manual_profile(
            hostname=hostname,
            vcpus=vcpus,
            memory_mb=memory_mb,
            os_type=os_type,
            architecture=architecture,
            **kwargs,
        )

    # -- Compatibility evaluation -------------------------------------------

    def check_vm_size(
        self, profile: OnPremVMProfile, vm_size_name: str
    ) -> Optional[CompatibilityResult]:
        """Evaluate compatibility against a specific VM size by name."""
        vm = self._catalog.get_by_name(vm_size_name)
        if vm is None:
            return None
        return evaluate_compatibility(profile, vm)

    def recommend(self, profile: OnPremVMProfile) -> MigrationRecommendation:
        """Evaluate all E-series sizes and return ranked recommendations."""
        return recommend_sizes(profile, self._catalog)

    # -- SDK compatibility --------------------------------------------------

    def as_compute_client(self) -> DigitalTwinComputeManagementClient:
        """Return an SDK-compatible compute client backed by this twin."""
        return DigitalTwinComputeManagementClient(
            series_filter=self._catalog.series_names
        )

    # -- Reporting ----------------------------------------------------------

    def generate_report(self, recommendation: MigrationRecommendation) -> str:
        """Produce a human-readable text report from a recommendation."""
        lines = [
            "=" * 72,
            "Azure E-Series Digital Twin  --  Migration Compatibility Report",
            "=" * 72,
            "",
            f"On-Premises Host:  {recommendation.on_prem.hostname}",
            f"  vCPUs:           {recommendation.on_prem.vcpus}",
            f"  Memory:          {recommendation.on_prem.memory_mb} MB "
            f"({recommendation.on_prem.memory_mb // 1024} GB)",
            f"  Architecture:    {recommendation.on_prem.architecture.value}",
            f"  Data disks:      {recommendation.on_prem.data_disks_count}",
            f"  OS:              {recommendation.on_prem.os_type}",
            "",
        ]

        if recommendation.best_fit:
            bf = recommendation.best_fit
            lines += [
                "-" * 72,
                "BEST FIT",
                "-" * 72,
                bf.summary(),
                "",
            ]

        if recommendation.compatible_sizes:
            lines += [
                "-" * 72,
                f"ALL COMPATIBLE SIZES  ({len(recommendation.compatible_sizes)} found)",
                "-" * 72,
            ]
            for r in recommendation.compatible_sizes:
                vm = r.vm_size
                lines.append(
                    f"  {vm.name:<30s}  {vm.number_of_cores:>3d} vCPUs  "
                    f"{vm.memory_in_mb // 1024:>5d} GB  [{r.status.value}]"
                )
            lines.append("")
        else:
            lines += [
                "-" * 72,
                "NO COMPATIBLE E-SERIES SIZES FOUND",
                "-" * 72,
                "Consider N-series (GPU), M-series (large memory), or",
                "splitting the workload across multiple VMs.",
                "",
            ]

        lines += [
            "=" * 72,
            f"Total E-series sizes evaluated: "
            f"{len(recommendation.compatible_sizes) + len(recommendation.incompatible_sizes)}",
            f"Compatible: {len(recommendation.compatible_sizes)}  |  "
            f"Incompatible: {len(recommendation.incompatible_sizes)}",
            "=" * 72,
        ]
        return "\n".join(lines)
