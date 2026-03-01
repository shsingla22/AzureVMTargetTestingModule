"""Tests for the compatibility analyzer engine."""

import pytest

from azure_vm_digital_twin.compatibility_analyzer import (
    evaluate_compatibility,
    recommend_sizes,
)
from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import (
    CompatibilityStatus,
    OnPremVMProfile,
    ProcessorArchitecture,
)


def _make_profile(**overrides) -> OnPremVMProfile:
    defaults = dict(
        hostname="test-vm",
        vcpus=4,
        memory_mb=32 * 1024,
        os_type="Linux",
        architecture=ProcessorArchitecture.X86_64,
    )
    defaults.update(overrides)
    return OnPremVMProfile(**defaults)


class TestEvaluateCompatibility:
    def test_small_vm_compatible(self):
        profile = _make_profile(vcpus=2, memory_mb=8 * 1024)
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E2s_v5")
        result = evaluate_compatibility(profile, vm)
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert result.is_compatible

    def test_oversized_vm_incompatible(self):
        profile = _make_profile(vcpus=256, memory_mb=2048 * 1024)
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E2s_v5")
        result = evaluate_compatibility(profile, vm)
        assert result.status == CompatibilityStatus.INCOMPATIBLE
        assert not result.is_compatible

    def test_architecture_mismatch_warning(self):
        profile = _make_profile(
            vcpus=2, memory_mb=8 * 1024,
            architecture=ProcessorArchitecture.ARM64,
        )
        catalog = ESeriesCatalog()
        # Esv5 is x86-64, profile is ARM64
        vm = catalog.get_by_name("Standard_E2s_v5")
        result = evaluate_compatibility(profile, vm)
        assert result.status == CompatibilityStatus.COMPATIBLE_WITH_WARNINGS

    def test_arm64_on_arm64_compatible(self):
        profile = _make_profile(
            vcpus=2, memory_mb=8 * 1024,
            architecture=ProcessorArchitecture.ARM64,
        )
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E2ps_v6")
        result = evaluate_compatibility(profile, vm)
        assert result.status == CompatibilityStatus.COMPATIBLE

    def test_gpu_required_always_fails(self):
        profile = _make_profile(vcpus=2, memory_mb=8 * 1024, gpu_required=True)
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E96s_v5")
        result = evaluate_compatibility(profile, vm)
        assert result.status == CompatibilityStatus.INCOMPATIBLE
        gpu_detail = [d for d in result.details if d.dimension == "GPU"][0]
        assert not gpu_detail.passed
        assert "N-series" in gpu_detail.message

    def test_temp_disk_required(self):
        profile = _make_profile(
            vcpus=2, memory_mb=8 * 1024, requires_temp_disk=True,
        )
        catalog = ESeriesCatalog()
        # Esv5 has no temp disk
        vm_no_temp = catalog.get_by_name("Standard_E2s_v5")
        result = evaluate_compatibility(profile, vm_no_temp)
        temp_detail = [d for d in result.details if d.dimension == "Temp disk"][0]
        assert not temp_detail.passed

        # Edsv5 has temp disk
        vm_temp = catalog.get_by_name("Standard_E2ds_v5")
        result2 = evaluate_compatibility(profile, vm_temp)
        temp_detail2 = [d for d in result2.details if d.dimension == "Temp disk"][0]
        assert temp_detail2.passed

    def test_iops_requirement(self):
        profile = _make_profile(vcpus=2, memory_mb=8 * 1024, required_iops=100000)
        catalog = ESeriesCatalog()
        vm_small = catalog.get_by_name("Standard_E2s_v5")
        result = evaluate_compatibility(profile, vm_small)
        iops_detail = [d for d in result.details if d.dimension == "IOPS"][0]
        assert not iops_detail.passed

    def test_nics_requirement(self):
        profile = _make_profile(vcpus=2, memory_mb=8 * 1024, required_nics=8)
        catalog = ESeriesCatalog()
        vm_small = catalog.get_by_name("Standard_E2s_v5")  # max 2 NICs
        result = evaluate_compatibility(profile, vm_small)
        nic_detail = [d for d in result.details if d.dimension == "NICs"][0]
        assert not nic_detail.passed

    def test_summary_contains_all_dimensions(self):
        profile = _make_profile(vcpus=4, memory_mb=32 * 1024)
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E4s_v5")
        result = evaluate_compatibility(profile, vm)
        summary = result.summary()
        assert "vCPUs" in summary
        assert "Memory" in summary
        assert "PASS" in summary


class TestRecommendSizes:
    def test_small_workload_has_many_compatible(self):
        profile = _make_profile(vcpus=2, memory_mb=8 * 1024)
        rec = recommend_sizes(profile)
        assert len(rec.compatible_sizes) > 10
        assert rec.best_fit is not None

    def test_best_fit_is_smallest_compatible(self):
        profile = _make_profile(vcpus=16, memory_mb=64 * 1024)
        rec = recommend_sizes(profile)
        assert rec.best_fit is not None
        bf = rec.best_fit.vm_size
        # Best fit should have >= 16 cores and >= 64 GB
        assert bf.number_of_cores >= 16
        assert bf.memory_in_mb >= 64 * 1024
        # And should be the smallest among compatible
        for other in rec.compatible_sizes[1:]:
            assert other.vm_size.memory_in_mb >= bf.memory_in_mb

    def test_impossible_workload_no_compatible(self):
        profile = _make_profile(vcpus=512, memory_mb=4096 * 1024)
        rec = recommend_sizes(profile)
        assert len(rec.compatible_sizes) == 0
        assert rec.best_fit is None

    def test_with_series_filter(self):
        profile = _make_profile(vcpus=4, memory_mb=16 * 1024)
        catalog = ESeriesCatalog(series_filter=["Esv5"])
        rec = recommend_sizes(profile, catalog=catalog)
        for r in rec.compatible_sizes:
            assert r.vm_size.series == "Esv5"
