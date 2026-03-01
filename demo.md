# Azure E-Series Digital Twin - Migration Compatibility Demo

*2026-03-01T01:58:20Z by Showboat 0.6.1*
<!-- showboat-id: 9bbdc6ed-79ca-41d2-ba65-f366c3d0deb2 -->

This demo showcases the Azure E-Series VM Digital Twin module. It validates whether an on-premises VM can successfully migrate to Azure E-series (memory-optimized) VMs by checking vCPUs, memory, storage, network, and architecture compatibility against a comprehensive catalog of 70+ E-series sizes across 8 sub-series (Esv5, Edsv5, Easv5, Eadsv5, Easv6, Epsv5, Epsv6, Esv7).

## 1. Catalog Overview - Exploring available E-series VM sizes

```bash
PYTHONPATH=/home/user/AzureVMTargetTestingModule/src python3 -c '
from azure_vm_digital_twin import ESeriesCatalog

catalog = ESeriesCatalog()
print("Total E-series VM sizes in catalog:", catalog.count())
print("Sub-series:", catalog.series_names)
print()
print("Sample sizes per series:")
for series in catalog.series_names:
    sizes = catalog.get_series(series)
    first = sizes[0]
    last = sizes[-1]
    print(f"  {series}: {len(sizes)} sizes, {first.name} ({first.number_of_cores} vCPUs, {first.memory_in_mb//1024} GB) ... {last.name} ({last.number_of_cores} vCPUs, {last.memory_in_mb//1024} GB)")
'
```

```output
Total E-series VM sizes in catalog: 63
Sub-series: ['Esv5', 'Edsv5', 'Easv5', 'Eadsv5', 'Easv6', 'Epsv5', 'Epsv6', 'Esv7']

Sample sizes per series:
  Esv5: 10 sizes, Standard_E2s_v5 (2 vCPUs, 16 GB) ... Standard_E104s_v5 (104 vCPUs, 672 GB)
  Edsv5: 8 sizes, Standard_E2ds_v5 (2 vCPUs, 16 GB) ... Standard_E96ds_v5 (96 vCPUs, 672 GB)
  Easv5: 8 sizes, Standard_E2as_v5 (2 vCPUs, 16 GB) ... Standard_E96as_v5 (96 vCPUs, 672 GB)
  Eadsv5: 7 sizes, Standard_E2ads_v5 (2 vCPUs, 16 GB) ... Standard_E96ads_v5 (96 vCPUs, 672 GB)
  Easv6: 8 sizes, Standard_E2as_v6 (2 vCPUs, 16 GB) ... Standard_E96as_v6 (96 vCPUs, 672 GB)
  Epsv5: 5 sizes, Standard_E2ps_v5 (2 vCPUs, 16 GB) ... Standard_E32ps_v5 (32 vCPUs, 208 GB)
  Epsv6: 8 sizes, Standard_E2ps_v6 (2 vCPUs, 16 GB) ... Standard_E96ps_v6 (96 vCPUs, 672 GB)
  Esv7: 9 sizes, Standard_E2s_v7 (2 vCPUs, 16 GB) ... Standard_E128s_v7 (128 vCPUs, 1024 GB)
```

## 2. SDK Compatibility - Drop-in replacement for azure-mgmt-compute

```bash
python3 demo_scripts/sdk_compat_demo.py
```

```output
Listing VM sizes (azure-mgmt-compute compatible interface):
------------------------------------------------------------------------
  Standard_E2s_v5                   2 cores    16384 MB  disks=4
  Standard_E4s_v5                   4 cores    32768 MB  disks=8
  Standard_E8s_v5                   8 cores    65536 MB  disks=16
  Standard_E16s_v5                 16 cores   131072 MB  disks=32
  Standard_E20s_v5                 20 cores   163840 MB  disks=32
  Standard_E32s_v5                 32 cores   262144 MB  disks=32
  Standard_E48s_v5                 48 cores   393216 MB  disks=32
  Standard_E64s_v5                 64 cores   524288 MB  disks=32
  Standard_E96s_v5                 96 cores   688128 MB  disks=64
  Standard_E104s_v5               104 cores   688128 MB  disks=64
  ... and 53 more sizes
```

## 3. Migration Compatibility Analysis - Validating an on-prem database server

```bash
python3 demo_scripts/migration_demo.py
```

```output
========================================================================
Azure E-Series Digital Twin  --  Migration Compatibility Report
========================================================================

On-Premises Host:  oltp-db-prod-01
  vCPUs:           32
  Memory:          262144 MB (256 GB)
  Architecture:    x86-64
  Data disks:      12
  OS:              Linux

------------------------------------------------------------------------
BEST FIT
------------------------------------------------------------------------
VM Size: Standard_E32s_v5
Status:  compatible
Message: Standard_E32s_v5 fully meets all requirements

Details:
  [PASS] vCPUs: need 32, have 32
  [PASS] Memory (MB): need 262144, have 262144
  [PASS] Data disks: need 12, have 32
  [PASS] IOPS: need 50000, have 51200
  [PASS] Storage throughput (MBps): need 800, have 865
  [PASS] NICs: need 2, have 8
  [PASS] Network bandwidth (Mbps): need none specified, have 16000
  [PASS] Temp disk: need not required, have no
  [PASS] Premium IO: need required, have yes
  [PASS] Ultra SSD: need not required, have yes
  [PASS] Architecture: need x86-64, have x86-64
  [PASS] GPU: need not required, have none (E-series is CPU-only)

------------------------------------------------------------------------
ALL COMPATIBLE SIZES  (27 found)
------------------------------------------------------------------------
  Standard_E32s_v5                 32 vCPUs    256 GB  [compatible]
  Standard_E32ds_v5                32 vCPUs    256 GB  [compatible]
  Standard_E32as_v6                32 vCPUs    256 GB  [compatible]
  Standard_E32ps_v6                32 vCPUs    256 GB  [compatible_with_warnings]
  Standard_E32s_v7                 32 vCPUs    256 GB  [compatible]
  Standard_E48s_v5                 48 vCPUs    384 GB  [compatible]
  Standard_E48ds_v5                48 vCPUs    384 GB  [compatible]
  Standard_E48as_v5                48 vCPUs    384 GB  [compatible]
  Standard_E48as_v6                48 vCPUs    384 GB  [compatible]
  Standard_E48ps_v6                48 vCPUs    384 GB  [compatible_with_warnings]
  Standard_E48s_v7                 48 vCPUs    384 GB  [compatible]
  Standard_E64s_v5                 64 vCPUs    512 GB  [compatible]
  Standard_E64ds_v5                64 vCPUs    512 GB  [compatible]
  Standard_E64as_v5                64 vCPUs    512 GB  [compatible]
  Standard_E64ads_v5               64 vCPUs    512 GB  [compatible]
  Standard_E64as_v6                64 vCPUs    512 GB  [compatible]
  Standard_E64ps_v6                64 vCPUs    512 GB  [compatible_with_warnings]
  Standard_E64s_v7                 64 vCPUs    512 GB  [compatible]
  Standard_E96s_v5                 96 vCPUs    672 GB  [compatible]
  Standard_E96ds_v5                96 vCPUs    672 GB  [compatible]
  Standard_E96as_v5                96 vCPUs    672 GB  [compatible]
  Standard_E96ads_v5               96 vCPUs    672 GB  [compatible]
  Standard_E96as_v6                96 vCPUs    672 GB  [compatible]
  Standard_E96ps_v6                96 vCPUs    672 GB  [compatible_with_warnings]
  Standard_E104s_v5               104 vCPUs    672 GB  [compatible]
  Standard_E96s_v7                 96 vCPUs    768 GB  [compatible]
  Standard_E128s_v7               128 vCPUs   1024 GB  [compatible]

========================================================================
Total E-series sizes evaluated: 63
Compatible: 27  |  Incompatible: 36
========================================================================
```

## 4. Single Size Check - Testing a specific VM size against requirements

```bash
python3 demo_scripts/single_check_demo.py
```

```output
VM Size: Standard_E8s_v5
Status:  compatible
Message: Standard_E8s_v5 fully meets all requirements

Details:
  [PASS] vCPUs: need 8, have 8
  [PASS] Memory (MB): need 32768, have 65536
  [PASS] Data disks: need 2, have 16
  [PASS] IOPS: need 6000, have 12800
  [PASS] Storage throughput (MBps): need none specified, have 290
  [PASS] NICs: need 2, have 4
  [PASS] Network bandwidth (Mbps): need none specified, have 12500
  [PASS] Temp disk: need not required, have no
  [PASS] Premium IO: need not required, have yes
  [PASS] Ultra SSD: need not required, have yes
  [PASS] Architecture: need x86-64, have x86-64
  [PASS] GPU: need not required, have none (E-series is CPU-only)

VM Size: Standard_E2s_v5
Status:  incompatible
Message: Standard_E2s_v5 incompatible: vCPUs, Memory (MB), IOPS

Details:
  [FAIL] vCPUs: need 8, have 2
         Insufficient vCPU count
  [FAIL] Memory (MB): need 32768, have 16384
         Insufficient memory
  [PASS] Data disks: need 2, have 4
  [FAIL] IOPS: need 6000, have 3750
         IOPS requirement not met
  [PASS] Storage throughput (MBps): need none specified, have 85
  [PASS] NICs: need 2, have 2
  [PASS] Network bandwidth (Mbps): need none specified, have 12500
  [PASS] Temp disk: need not required, have no
  [PASS] Premium IO: need not required, have yes
  [PASS] Ultra SSD: need not required, have yes
  [PASS] Architecture: need x86-64, have x86-64
  [PASS] GPU: need not required, have none (E-series is CPU-only)
```

## 5. Test Suite - All 54 tests passing

```bash
python3 demo_scripts/test_demo.py
```

```output
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /home/user/AzureVMTargetTestingModule
configfile: pyproject.toml
plugins: cov-7.0.0
collecting ... collected 54 items

tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_small_vm_compatible PASSED [  1%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_oversized_vm_incompatible PASSED [  3%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_architecture_mismatch_warning PASSED [  5%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_arm64_on_arm64_compatible PASSED [  7%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_gpu_required_always_fails PASSED [  9%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_temp_disk_required PASSED [ 11%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_iops_requirement PASSED [ 12%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_nics_requirement PASSED [ 14%]
tests/test_compatibility_analyzer.py::TestEvaluateCompatibility::test_summary_contains_all_dimensions PASSED [ 16%]
tests/test_compatibility_analyzer.py::TestRecommendSizes::test_small_workload_has_many_compatible PASSED [ 18%]
tests/test_compatibility_analyzer.py::TestRecommendSizes::test_best_fit_is_smallest_compatible PASSED [ 20%]
tests/test_compatibility_analyzer.py::TestRecommendSizes::test_impossible_workload_no_compatible PASSED [ 22%]
tests/test_compatibility_analyzer.py::TestRecommendSizes::test_with_series_filter PASSED [ 24%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_instantiation PASSED [ 25%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_instantiation_with_filter PASSED [ 27%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_profile_from_specs PASSED [ 29%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_check_vm_size_compatible PASSED [ 31%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_check_vm_size_incompatible PASSED [ 33%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_check_vm_size_not_found PASSED [ 35%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_recommend PASSED [ 37%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_recommend_sorts_by_size PASSED [ 38%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_as_compute_client PASSED [ 40%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_generate_report PASSED [ 42%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_generate_report_no_compatible PASSED [ 44%]
tests/test_digital_twin.py::TestAzureESeriesDigitalTwin::test_end_to_end_migration_scenario PASSED [ 46%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_catalog_contains_all_series PASSED [ 48%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_catalog_has_reasonable_count PASSED [ 50%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_list_iterates_all_sizes PASSED [ 51%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_by_name_found PASSED [ 53%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_by_name_not_found PASSED [ 55%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_series PASSED [ 57%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_cores PASSED [ 59%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_cores_range PASSED [ 61%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_memory_gb PASSED [ 62%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_architecture_x86 PASSED [ 64%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_architecture_arm64 PASSED [ 66%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_series_filter PASSED [ 68%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_vm_size_sdk_dict PASSED [ 70%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_esv7_latest_gen_present PASSED [ 72%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_memory_to_core_ratio PASSED [ 74%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_instantiate_without_credentials PASSED [ 75%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_instantiate_with_dummy_credentials PASSED [ 77%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_context_manager PASSED [ 79%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_virtual_machine_sizes_attribute PASSED [ 81%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_list_returns_iterable PASSED [ 83%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_list_location_is_ignored PASSED [ 85%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_vm_size_has_sdk_fields PASSED [ 87%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_as_dict PASSED [ 88%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_series_filter PASSED [ 90%]
tests/test_sdk_compat.py::TestDigitalTwinComputeClient::test_catalog_access PASSED [ 92%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_typical_list_pattern PASSED [ 94%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_hardware_profile_pattern PASSED [ 96%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_size_comparison PASSED [ 98%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_repr PASSED  [100%]

============================== 54 passed in 0.14s ==============================
```

All 54 tests pass across 4 test modules covering the catalog, compatibility analyzer, SDK compatibility layer, and the digital twin orchestrator.
