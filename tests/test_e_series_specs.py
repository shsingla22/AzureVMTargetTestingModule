"""Tests for the E-series VM catalog."""

import pytest

from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.models import ProcessorArchitecture


class TestESeriesCatalog:
    def test_catalog_contains_all_series(self):
        catalog = ESeriesCatalog()
        expected = {"Esv5", "Edsv5", "Easv5", "Eadsv5", "Easv6", "Epsv5", "Epsv6", "Esv7"}
        assert set(catalog.series_names) == expected

    def test_catalog_has_reasonable_count(self):
        catalog = ESeriesCatalog()
        assert catalog.count() >= 60

    def test_list_iterates_all_sizes(self):
        catalog = ESeriesCatalog()
        sizes = list(catalog.list())
        assert len(sizes) == catalog.count()

    def test_get_by_name_found(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E8s_v5")
        assert vm is not None
        assert vm.number_of_cores == 8
        assert vm.memory_in_mb == 64 * 1024

    def test_get_by_name_not_found(self):
        catalog = ESeriesCatalog()
        assert catalog.get_by_name("NONEXISTENT") is None

    def test_get_series(self):
        catalog = ESeriesCatalog()
        esv5 = catalog.get_series("Esv5")
        assert len(esv5) >= 8
        assert all(vm.series == "Esv5" for vm in esv5)

    def test_filter_by_cores(self):
        catalog = ESeriesCatalog()
        large = catalog.filter_by_cores(64)
        assert all(vm.number_of_cores >= 64 for vm in large)

    def test_filter_by_cores_range(self):
        catalog = ESeriesCatalog()
        mid = catalog.filter_by_cores(8, 32)
        assert all(8 <= vm.number_of_cores <= 32 for vm in mid)

    def test_filter_by_memory_gb(self):
        catalog = ESeriesCatalog()
        big_mem = catalog.filter_by_memory_gb(256)
        assert all(vm.memory_in_mb >= 256 * 1024 for vm in big_mem)

    def test_filter_by_architecture_x86(self):
        catalog = ESeriesCatalog()
        x86 = catalog.filter_by_architecture(ProcessorArchitecture.X86_64)
        assert len(x86) > 0
        assert all(vm.architecture == ProcessorArchitecture.X86_64 for vm in x86)

    def test_filter_by_architecture_arm64(self):
        catalog = ESeriesCatalog()
        arm = catalog.filter_by_architecture(ProcessorArchitecture.ARM64)
        assert len(arm) > 0
        assert all(vm.architecture == ProcessorArchitecture.ARM64 for vm in arm)

    def test_series_filter(self):
        catalog = ESeriesCatalog(series_filter=["Esv5"])
        assert catalog.series_names == ["Esv5"]
        assert all(vm.series == "Esv5" for vm in catalog.list())

    def test_vm_size_sdk_dict(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E4s_v5")
        d = vm.as_sdk_dict()
        assert d["name"] == "Standard_E4s_v5"
        assert d["number_of_cores"] == 4
        assert d["memory_in_mb"] == 32 * 1024
        assert "max_data_disk_count" in d

    def test_esv7_latest_gen_present(self):
        catalog = ESeriesCatalog()
        vm = catalog.get_by_name("Standard_E128s_v7")
        assert vm is not None
        assert vm.number_of_cores == 128
        assert "Granite Rapids" in vm.processor

    def test_memory_to_core_ratio(self):
        """E-series VMs have at least ~6 GB per core."""
        catalog = ESeriesCatalog()
        for vm in catalog.list():
            ratio = (vm.memory_in_mb / 1024) / vm.number_of_cores
            assert ratio >= 6.0, f"{vm.name} has ratio {ratio:.1f} GB/core"
