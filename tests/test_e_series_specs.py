"""Tests for the E-series VM catalog."""

import pytest

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import ProcessorArchitecture


class TestESeriesCatalog:
    def test_catalog_contains_all_series(self):
        catalog = ESeriesCatalog()
        names = catalog.series_names
        assert "Esv5" in names
        assert "Edsv5" in names
        assert "Easv5" in names
        assert "Eadsv5" in names
        assert "Easv6" in names
        assert "Epsv5" in names
        assert "Epsv6" in names
        assert "Esv7" in names

    def test_catalog_has_reasonable_count(self):
        catalog = ESeriesCatalog()
        assert catalog.count() >= 60

    def test_list_iterates_all_sizes(self):
        catalog = ESeriesCatalog()
        sizes = list(catalog.list())
        assert len(sizes) == catalog.count()
        assert all(s.name.startswith("Standard_E") for s in sizes)

    def test_get_by_name_found(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E16s_v5")
        assert vm is not None
        assert vm.number_of_cores == 16
        assert vm.memory_in_mb == 128 * 1024

    def test_get_by_name_not_found(self):
        catalog = ESeriesCatalog()
        assert catalog.get_by_name("Standard_D4s_v5") is None

    def test_get_series(self):
        catalog = ESeriesCatalog()
        esv5 = catalog.get_series("Esv5")
        assert len(esv5) >= 8
        assert all(s.series == "Esv5" for s in esv5)

    def test_filter_by_cores(self):
        catalog = ESeriesCatalog()
        large = catalog.filter_by_cores(64)
        assert all(s.number_of_cores >= 64 for s in large)
        assert len(large) > 0

    def test_filter_by_cores_range(self):
        catalog = ESeriesCatalog()
        mid = catalog.filter_by_cores(8, 32)
        assert all(8 <= s.number_of_cores <= 32 for s in mid)

    def test_filter_by_memory_gb(self):
        catalog = ESeriesCatalog()
        big_mem = catalog.filter_by_memory_gb(256)
        assert all(s.memory_in_mb >= 256 * 1024 for s in big_mem)

    def test_filter_by_architecture_x86(self):
        catalog = ESeriesCatalog()
        x86 = catalog.filter_by_architecture(ProcessorArchitecture.X86_64)
        assert len(x86) > 0
        assert all(s.architecture == ProcessorArchitecture.X86_64 for s in x86)

    def test_filter_by_architecture_arm64(self):
        catalog = ESeriesCatalog()
        arm = catalog.filter_by_architecture(ProcessorArchitecture.ARM64)
        assert len(arm) > 0
        assert all(s.architecture == ProcessorArchitecture.ARM64 for s in arm)

    def test_series_filter(self):
        catalog = ESeriesCatalog(series_filter=["Esv5"])
        assert catalog.series_names == ["Esv5"]
        assert all(s.series == "Esv5" for s in catalog.list())

    def test_vm_size_sdk_dict(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E2s_v5")
        d = vm.as_sdk_dict()
        assert d["name"] == "Standard_E2s_v5"
        assert d["number_of_cores"] == 2
        assert d["memory_in_mb"] == 16 * 1024
        assert "max_data_disk_count" in d
        assert "os_disk_size_in_mb" in d

    def test_esv7_latest_gen_present(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E128s_v7")
        assert vm is not None
        assert vm.number_of_cores == 128
        assert "Granite Rapids" in vm.processor

    def test_memory_to_core_ratio(self):
        """E-series VMs have a high memory-to-core ratio (>=8 GB/core)."""
        catalog = ESeriesCatalog()
        for vm in catalog.list():
            gb_per_core = (vm.memory_in_mb / 1024) / vm.number_of_cores
            assert gb_per_core >= 6.0, (
                f"{vm.name}: ratio {gb_per_core:.1f} GB/core is too low for E-series"
            )
