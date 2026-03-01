# Azure E-Series Digital Twin — Workload Simulation Demo

*2026-03-01T05:40:13Z by Showboat 0.6.1*
<!-- showboat-id: c93ef798-3548-4b54-a9e7-022a1eea5eaf -->

This module is a digital twin of Azure E-series (memory-optimized) VMs. It simulates the resource constraints of any E-series SKU — CPU cores, memory, IOPS, network bandwidth — using Linux cgroups, so you can run real customer workloads inside those limits and observe how they behave before committing to a migration.

## 1. Create a digital-twin VM and enforce resource constraints

```bash
/usr/local/bin/python demo_scripts/01_create_and_start.py
```

```output
Created VM: db-test-01
  SKU:      Standard_E8s_v5
  vCPUs:    8
  Memory:   64 GB
  Max IOPS: 12800
  State:    PowerState/stopped

Started VM — enforcement method: process
  CPU limit:    8 cores
  Memory limit: 64 GB
  IOPS limit:   12800
  State:        PowerState/running
```

## 2. Run a workload under E-series resource constraints

```bash
/usr/local/bin/python demo_scripts/02_run_workload.py
```

```output
Workload Simulation Result: PASSED
  VM Size:        Standard_E4s_v5
  Command:        python3 -c import math; [math.factorial(5000) for _ in range(200)]
  Duration:       0.17s
  Exit code:      0

  CPU:
    Peak:         0.0%
    Average:      0.0%
    Throttled:    0 periods (0.000s)

  Memory:
    Limit:        32768 MB
    Peak:         0.0 MB (0.0%)
    OOM kills:    0

  I/O:
    Read:         0 bytes (0 ops)
    Write:        0 bytes (0 ops)
    Avg IOPS:     0.0

  Enforced constraints:
    cpu_cores: 4
    cpu_quota_us: 400000/100000
    memory_limit_mb: 32768
    io_max_iops: 6400
    io_max_bps: 152043520
    net_rate_mbit: 12500
    enforcement: process
```

## 3. Azure SDK-compatible VM lifecycle (azure-mgmt-compute pattern)

```bash
/usr/local/bin/python demo_scripts/03_sdk_lifecycle.py
```

```output
Creating VM via SDK-compatible interface...
  Created: web-server (Standard_E16s_v5, 16 vCPUs)
  State:   PowerState/running
  Instance view: ['PowerState/running', 'ProvisioningState/succeeded']

Deallocating VM...
  State: PowerState/deallocated

Restarting VM...
  State: PowerState/running

Listing VMs in resource group:
  web-server: Standard_E16s_v5 [PowerState/running]

VM deleted.
```

## 4. Memory stress test — observe behavior under constraints

```bash
/usr/local/bin/python demo_scripts/04_memory_stress.py
```

```output
50 MB allocation: PASSED
  Peak memory: 0.0 MB
  OOM kills:   0

========================================================================
Azure E-Series Digital Twin — Workload Simulation Report
========================================================================

VM Name:       mem-test
VM Size:       Standard_E2s_v5  (Esv5)
  vCPUs:       2
  Memory:      16384 MB (16 GB)
  Max IOPS:    3750
  Bandwidth:   12500 Mbps
  Power state: PowerState/running
  Enforcement: process

Workloads run: 1  (passed=1, failed=0)

------------------------------------------------------------------------
Workload #1
------------------------------------------------------------------------
Workload Simulation Result: PASSED
  VM Size:        Standard_E2s_v5
  Command:        python3 -c data = bytearray(50 * 1024 * 1024); print(f'Allocated {len(data) // (1024*1024)} MB')
  Duration:       0.07s
  Exit code:      0

  CPU:
    Peak:         0.0%
    Average:      0.0%
    Throttled:    0 periods (0.000s)

  Memory:
    Limit:        16384 MB
    Peak:         0.0 MB (0.0%)
    OOM kills:    0

  I/O:
    Read:         0 bytes (0 ops)
    Write:        0 bytes (0 ops)
    Avg IOPS:     0.0

  Enforced constraints:
    cpu_cores: 2
    cpu_quota_us: 200000/100000
    memory_limit_mb: 16384
    io_max_iops: 3750
    io_max_bps: 89128960
    net_rate_mbit: 12500
    enforcement: process

========================================================================
```

## 5. Full test suite — 81 tests passing

```bash
/usr/local/bin/python demo_scripts/05_run_tests.py
```

```output
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /home/user/AzureVMTargetTestingModule
configfile: pyproject.toml
plugins: cov-7.0.0
collecting ... collected 81 items

tests/test_digital_twin.py::TestVMLifecycle::test_create_vm PASSED       [  1%]
tests/test_digital_twin.py::TestVMLifecycle::test_create_vm_bad_size_raises PASSED [  2%]
tests/test_digital_twin.py::TestVMLifecycle::test_create_duplicate_raises PASSED [  3%]
tests/test_digital_twin.py::TestVMLifecycle::test_start_vm PASSED        [  4%]
tests/test_digital_twin.py::TestVMLifecycle::test_stop_vm PASSED         [  6%]
tests/test_digital_twin.py::TestVMLifecycle::test_deallocate_vm PASSED   [  7%]
tests/test_digital_twin.py::TestVMLifecycle::test_delete_vm PASSED       [  8%]
tests/test_digital_twin.py::TestVMLifecycle::test_resize_vm PASSED       [  9%]
tests/test_digital_twin.py::TestVMLifecycle::test_resize_running_raises PASSED [ 11%]
tests/test_digital_twin.py::TestVMLifecycle::test_list_vms PASSED        [ 12%]
tests/test_digital_twin.py::TestWorkloadExecution::test_run_simple_command PASSED [ 13%]
tests/test_digital_twin.py::TestWorkloadExecution::test_run_script PASSED [ 14%]
tests/test_digital_twin.py::TestWorkloadExecution::test_run_on_stopped_vm_raises PASSED [ 16%]
tests/test_digital_twin.py::TestWorkloadExecution::test_run_nonexistent_vm_raises PASSED [ 17%]
tests/test_digital_twin.py::TestWorkloadExecution::test_run_failing_command PASSED [ 18%]
tests/test_digital_twin.py::TestWorkloadExecution::test_workload_with_timeout PASSED [ 19%]
tests/test_digital_twin.py::TestWorkloadExecution::test_workload_records_on_vm PASSED [ 20%]
tests/test_digital_twin.py::TestWorkloadExecution::test_metrics_has_duration PASSED [ 22%]
tests/test_digital_twin.py::TestWorkloadExecution::test_enforced_constraints_in_result PASSED [ 23%]
tests/test_digital_twin.py::TestWorkloadExecution::test_cpu_intensive_workload_produces_metrics PASSED [ 24%]
tests/test_digital_twin.py::TestReporting::test_generate_report PASSED   [ 25%]
tests/test_digital_twin.py::TestReporting::test_generate_report_no_workloads PASSED [ 27%]
tests/test_digital_twin.py::TestReporting::test_generate_report_unknown_vm PASSED [ 28%]
tests/test_digital_twin.py::TestReporting::test_workload_result_summary PASSED [ 29%]
tests/test_digital_twin.py::TestVMInstance::test_vm_id_format PASSED     [ 30%]
tests/test_digital_twin.py::TestVMInstance::test_vm_as_sdk_dict PASSED   [ 32%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_catalog_contains_all_series PASSED [ 33%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_catalog_has_reasonable_count PASSED [ 34%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_list_iterates_all_sizes PASSED [ 35%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_by_name_found PASSED [ 37%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_by_name_not_found PASSED [ 38%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_get_series PASSED [ 39%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_cores PASSED [ 40%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_cores_range PASSED [ 41%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_memory_gb PASSED [ 43%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_architecture_x86 PASSED [ 44%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_filter_by_architecture_arm64 PASSED [ 45%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_series_filter PASSED [ 46%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_vm_size_sdk_dict PASSED [ 48%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_esv7_latest_gen_present PASSED [ 49%]
tests/test_e_series_specs.py::TestESeriesCatalog::test_memory_to_core_ratio PASSED [ 50%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_instantiate_without_credentials PASSED [ 51%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_instantiate_with_dummy_credentials PASSED [ 53%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_context_manager PASSED [ 54%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_list_returns_iterable PASSED [ 55%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_list_location_is_ignored PASSED [ 56%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_vm_size_has_sdk_fields PASSED [ 58%]
tests/test_sdk_compat.py::TestVirtualMachineSizes::test_as_dict PASSED   [ 59%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_has_virtual_machines_attribute PASSED [ 60%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_begin_create_or_update PASSED [ 61%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_begin_create_azure_style_params PASSED [ 62%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_get_vm PASSED [ 64%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_get_nonexistent_returns_none PASSED [ 65%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_begin_deallocate PASSED [ 66%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_begin_delete PASSED [ 67%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_list_vms_by_resource_group PASSED [ 69%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_list_all PASSED [ 70%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_instance_view PASSED [ 71%]
tests/test_sdk_compat.py::TestVirtualMachinesOperations::test_poller_interface PASSED [ 72%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_typical_list_sizes_pattern PASSED [ 74%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_typical_create_vm_pattern PASSED [ 75%]
tests/test_sdk_compat.py::TestSDKPatternCompatibility::test_typical_lifecycle_pattern PASSED [ 76%]
tests/test_simulator.py::TestResourceGovernor::test_enforcement_method PASSED [ 77%]
tests/test_simulator.py::TestResourceGovernor::test_create_sandbox PASSED [ 79%]
tests/test_simulator.py::TestResourceGovernor::test_constraints_as_dict PASSED [ 80%]
tests/test_simulator.py::TestResourceGovernor::test_destroy_nonexistent_sandbox_is_safe PASSED [ 81%]
tests/test_simulator.py::TestResourceGovernor::test_get_constraints PASSED [ 82%]
tests/test_simulator.py::TestResourceGovernor::test_get_constraints_after_destroy PASSED [ 83%]
tests/test_simulator.py::TestResourceGovernor::test_destroy_all PASSED   [ 85%]
tests/test_simulator.py::TestResourceGovernor::test_read_cpu_stats PASSED [ 86%]
tests/test_simulator.py::TestResourceGovernor::test_read_memory_stats PASSED [ 87%]
tests/test_simulator.py::TestNetworkGovernor::test_instantiation PASSED  [ 88%]
tests/test_simulator.py::TestNetworkGovernor::test_remove_nonexistent_is_safe PASSED [ 90%]
tests/test_simulator.py::TestNetworkGovernor::test_remove_all PASSED     [ 91%]
tests/test_simulator.py::TestVMInstanceManager::test_create_instance PASSED [ 92%]
tests/test_simulator.py::TestVMInstanceManager::test_start_instance PASSED [ 93%]
tests/test_simulator.py::TestVMInstanceManager::test_stop_instance PASSED [ 95%]
tests/test_simulator.py::TestVMInstanceManager::test_delete_instance PASSED [ 96%]
tests/test_simulator.py::TestVMInstanceManager::test_resize_instance PASSED [ 97%]
tests/test_simulator.py::TestVMInstanceManager::test_list_instances PASSED [ 98%]
tests/test_simulator.py::TestVMInstanceManager::test_cleanup_releases_all PASSED [100%]

============================== 81 passed in 1.73s ==============================
```
