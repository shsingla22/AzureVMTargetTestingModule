"""Tests for the high-level AzureESeriesDigitalTwin orchestrator."""

import pytest

from azure_vm_digital_twin.digital_twin import AzureESeriesDigitalTwin
from azure_vm_digital_twin.models import (
    CompatibilityStatus,
    ProcessorArchitecture,
)


class TestAzureESeriesDigitalTwin:
    def test_instantiation(self):
        twin = AzureESeriesDigitalTwin()
        assert twin.catalog.count() > 0

    def test_instantiation_with_filter(self):
        twin = AzureESeriesDigitalTwin(series_filter=["Esv5", "Edsv5"])
        assert set(twin.catalog.series_names) == {"Esv5", "Edsv5"}

    def test_profile_from_specs(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(
            hostname="db-prod-01",
            vcpus=16,
            memory_mb=128 * 1024,
            data_disks_count=8,
            required_iops=25000,
        )
        assert profile.hostname == "db-prod-01"
        assert profile.vcpus == 16
        assert profile.memory_mb == 128 * 1024

    def test_check_vm_size_compatible(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(vcpus=4, memory_mb=16 * 1024)
        result = twin.check_vm_size(profile, "Standard_E4s_v5")
        assert result is not None
        assert result.is_compatible

    def test_check_vm_size_incompatible(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(vcpus=64, memory_mb=512 * 1024)
        result = twin.check_vm_size(profile, "Standard_E2s_v5")
        assert result is not None
        assert not result.is_compatible

    def test_check_vm_size_not_found(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(vcpus=2, memory_mb=8 * 1024)
        result = twin.check_vm_size(profile, "Standard_NONEXISTENT_v99")
        assert result is None

    def test_recommend(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(
            hostname="app-server",
            vcpus=8,
            memory_mb=64 * 1024,
        )
        rec = twin.recommend(profile)
        assert rec.best_fit is not None
        assert rec.best_fit.is_compatible
        assert len(rec.compatible_sizes) > 0

    def test_recommend_sorts_by_size(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(vcpus=4, memory_mb=16 * 1024)
        rec = twin.recommend(profile)
        memories = [r.vm_size.memory_in_mb for r in rec.compatible_sizes]
        assert memories == sorted(memories)

    def test_as_compute_client(self):
        twin = AzureESeriesDigitalTwin()
        client = twin.as_compute_client()
        sizes = list(client.virtual_machine_sizes.list("eastus"))
        assert len(sizes) == twin.catalog.count()

    def test_generate_report(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(
            hostname="sql-prod",
            vcpus=16,
            memory_mb=128 * 1024,
            data_disks_count=4,
        )
        rec = twin.recommend(profile)
        report = twin.generate_report(rec)
        assert "sql-prod" in report
        assert "BEST FIT" in report
        assert "COMPATIBLE" in report

    def test_generate_report_no_compatible(self):
        twin = AzureESeriesDigitalTwin()
        profile = twin.profile_from_specs(vcpus=1024, memory_mb=999999 * 1024)
        rec = twin.recommend(profile)
        report = twin.generate_report(rec)
        assert "NO COMPATIBLE" in report

    def test_end_to_end_migration_scenario(self):
        """Full end-to-end: profile -> recommend -> report."""
        twin = AzureESeriesDigitalTwin()

        # Simulate a mid-size database server
        profile = twin.profile_from_specs(
            hostname="oltp-db-01",
            vcpus=32,
            memory_mb=256 * 1024,
            os_type="Linux",
            data_disks_count=16,
            required_iops=50000,
            required_throughput_mbps=800,
            required_nics=2,
            requires_premium_io=True,
        )

        rec = twin.recommend(profile)
        assert rec.best_fit is not None

        best = rec.best_fit.vm_size
        assert best.number_of_cores >= 32
        assert best.memory_in_mb >= 256 * 1024
        assert best.storage.max_data_disk_count >= 16
        assert best.storage.max_iops >= 50000

        report = twin.generate_report(rec)
        assert "oltp-db-01" in report
        assert best.name in report
