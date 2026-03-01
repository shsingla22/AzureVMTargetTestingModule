# Design Document: Azure E-Series VM Digital Twin

## 1. Problem Statement

Customers migrating on-premises workloads to Azure need to answer:
**"How will my workload actually behave on a Standard_E16s_v5?"** — not
just "will it fit?", but will it be CPU-throttled, will it OOM, will
IOPS be a bottleneck?

Static capacity checks ("you need 16 cores and 128 GB, this SKU has
that") don't answer these questions.  You need to actually *run* the
workload under the target SKU's constraints and observe what happens.

## 2. Solution Overview

The digital twin creates a **resource-constrained sandbox** on the
current host that mirrors the exact limits of a chosen E-series Azure
VM SKU.  Customer workloads are executed inside this sandbox, and the
engine collects metrics on CPU throttling, memory pressure, OOM events,
and I/O throughput to determine whether the workload is viable.

```
┌───────────────────────────────────────────────────────────────┐
│                    AzureESeriesDigitalTwin                     │
│                     (digital_twin.py)                         │
│                                                               │
│  ┌─────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│  │ ESeriesCatalog│   │ VMInstanceManager │   │WorkloadRunner │  │
│  │ 63 VM sizes  │   │ create/start/stop │   │run inside     │  │
│  │ 8 sub-series │   │ resize/delete     │   │sandbox +      │  │
│  │              │   │                   │   │collect metrics │  │
│  └──────┬───────┘   └────────┬──────────┘   └───────┬───────┘  │
│         │                    │                      │          │
│         │           ┌────────▼──────────┐           │          │
│         │           │  ResourceGovernor  │◄──────────┘          │
│         │           │  (cgroup v2 /     │                      │
│         │           │   process-level)  │                      │
│         │           │                   │                      │
│         │           │  ┌─ cpu.max ────┐ │                      │
│         │           │  │ memory.max   │ │                      │
│         │           │  │ memory.swap  │ │                      │
│         │           │  │ io.max       │ │                      │
│         │           │  └──────────────┘ │                      │
│         │           └────────┬──────────┘                      │
│         │                    │                                 │
│         │           ┌────────▼──────────┐                      │
│         │           │ NetworkGovernor   │                      │
│         │           │ (tc tbf qdisc)    │                      │
│         │           └───────────────────┘                      │
│         │                                                      │
│  ┌──────▼──────────────────────────────────────────────────┐   │
│  │              SDK Compatibility Layer                     │   │
│  │  DigitalTwinComputeManagementClient                     │   │
│  │    .virtual_machine_sizes.list(location)                │   │
│  │    .virtual_machines.begin_create_or_update(rg, n, p)   │   │
│  │    .virtual_machines.begin_start / begin_deallocate     │   │
│  │    .virtual_machines.get / list / instance_view         │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## 3. Component Design

### 3.1 E-Series Catalog (`e_series_specs.py`)

**Purpose:** A complete, queryable database of every E-series VM SKU
with production-accurate specifications.

**Data per SKU:**
- `name` — e.g. `Standard_E32s_v5`
- `number_of_cores` — vCPU count
- `memory_in_mb` — RAM in megabytes
- `series` — sub-series identifier (Esv5, Edsv5, …)
- `processor` — physical CPU (Sapphire Rapids, EPYC Genoa, etc.)
- `architecture` — x86-64 or ARM64
- `storage.max_iops` — maximum I/O operations per second
- `storage.max_throughput_mbps` — maximum storage bandwidth
- `storage.has_temp_disk` / `temp_disk_size_gb` — local SSD
- `network.max_nics` — NIC count
- `network.expected_bandwidth_mbps` — network bandwidth cap

**Coverage:** 63 sizes across 8 sub-series, including the latest
generation (Esv7 with Granite Rapids up to 128 vCPUs / 1 TB).

**Query API:**
```python
catalog = ESeriesCatalog()
catalog.get_by_name("Standard_E16s_v5")      # exact lookup
catalog.filter_by_cores(16, 64)               # range query
catalog.filter_by_memory_gb(128)              # minimum memory
catalog.filter_by_architecture(ARM64)         # arch filter
catalog.get_series("Esv7")                    # series filter
```

### 3.2 Resource Governor (`simulator/resource_governor.py`)

**Purpose:** Enforce the target SKU's CPU, memory, and I/O limits on
the host machine using Linux kernel mechanisms.

**Primary enforcement: cgroup v2 (unified hierarchy)**

When the process runs as root on a host with cgroup v2 mounted at
`/sys/fs/cgroup`, the governor creates a sub-cgroup per VM and writes
the SKU limits into cgroup control files:

| SKU constraint | cgroup v2 knob | Example (E8s_v5) |
|---|---|---|
| 8 vCPUs | `cpu.max` | `800000 100000` (8 × 100ms period) |
| 64 GB RAM | `memory.max` | `68719476736` bytes |
| No swap | `memory.swap.max` | `0` |
| 12800 IOPS | `io.max` | `8:0 riops=12800 wiops=12800` |
| 290 MB/s throughput | `io.max` | `8:0 rbps=304087040 wbps=304087040` |

The CPU limit uses a quota/period model: `cpu.max = quota period`.
A quota of 800000µs over a 100000µs period means the cgroup can
consume at most 8 CPU-seconds per wall-second — exactly matching 8
vCPUs.  The kernel's CFS bandwidth controller throttles processes that
exceed this, and the throttling events are observable via `cpu.stat`:

```
nr_throttled 142
throttled_usec 3200000
```

Memory enforcement is hard-limit: `memory.max` caps RSS + page cache.
If a workload exceeds this, the kernel OOM-killer activates, and the
kill count is readable from `memory.events`:

```
oom_kill 1
```

Swap is disabled (`memory.swap.max = 0`) to match Azure VM behavior
where swap is not provisioned by default.

**Fallback enforcement: process-level limits**

When cgroup v2 is unavailable (containers, non-root, older kernels),
the governor falls back to:

| Constraint | Mechanism |
|---|---|
| CPU cores | `os.sched_setaffinity(pid, cpuset)` — pins process to N cores |
| Memory | `resource.setrlimit(RLIMIT_AS, limit)` — virtual address space cap |

This provides weaker isolation (no throttling metrics, no OOM kill
tracking) but still enforces the upper bounds.

**Detection logic:**
```
cgroup v2 available?
  └─ /sys/fs/cgroup/cgroup.controllers exists?
  └─ Can create sub-cgroup?  (mkdir test, rmdir test)
  └─ Yes → use cgroupv2     No → use process-level
```

### 3.3 Network Governor (`simulator/network_governor.py`)

**Purpose:** Enforce the SKU's network bandwidth limit.

Uses Linux `tc` (traffic control) with a Token Bucket Filter (tbf)
qdisc on the specified network interface:

```bash
tc qdisc add dev eth0 root tbf \
    rate 12500mbit \
    burst 12500000 \
    latency 50ms
```

Falls back to no-op when `tc` is not available (detected via
`shutil.which("tc")`).

### 3.4 VM Instance Manager (`simulator/vm_instance.py`)

**Purpose:** Manage the complete lifecycle of digital-twin VM
instances, mapping state transitions to sandbox operations.

**State machine:**

```
                create()
  (none) ───────────────►  STOPPED
                              │
                    start()   │   deallocate()
                              ▼       ▲
                           RUNNING ───┘
                              │
                    stop()    │
                              ▼
                           STOPPED
                              │
                    delete()  │
                              ▼
                           (none)
```

**State transition → sandbox action:**

| Transition | Action |
|---|---|
| `create()` | Register VM in memory, resolve SKU from catalog |
| `start()` | Call `ResourceGovernor.create_sandbox()` — writes cgroup limits; call `NetworkGovernor.apply_limit()` |
| `stop()` | Call `ResourceGovernor.destroy_sandbox()` — removes cgroup; call `NetworkGovernor.remove_limit()` |
| `deallocate()` | Same as stop, then set state to DEALLOCATED |
| `resize()` | Requires STOPPED state. Swaps `vm.vm_size` to new SKU. Next `start()` uses new limits |
| `delete()` | Stops if running, removes from registry |

### 3.5 Workload Runner (`workload/runner.py`)

**Purpose:** Execute real commands inside a VM's resource sandbox and
collect performance metrics throughout execution.

**Execution flow:**

```
1. Validate VM exists and is RUNNING
2. subprocess.Popen(command)          ← spawn workload
3. governor.apply_to_pid(vm, pid)     ← move into cgroup
4. Start MetricsCollector thread      ← background sampling
5. proc.communicate(timeout)          ← wait for completion
6. Stop collector, take final sample
7. Aggregate snapshots → SimulationMetrics
8. Return WorkloadResult
```

**Step 3 (apply_to_pid)** is critical: it writes the child PID to
`/sys/fs/cgroup/azure-dt-{name}/cgroup.procs`, which moves the
process and all its threads into the constrained cgroup.  From that
point on, the kernel enforces CPU, memory, and I/O limits on it.

**Step 4 (background sampling)** runs in a daemon thread that calls
`collector.sample()` every 0.5s (configurable).  Each sample reads:
- Process CPU% and RSS via `psutil.Process(pid)`
- CPU throttling from `cpu.stat` (throttled periods, throttled µs)
- Memory from `memory.current` and `memory.events` (OOM kill count)
- I/O from `io.stat` (read/write bytes and ops)

### 3.6 Metrics Collector (`workload/metrics.py`)

**Purpose:** Sample and aggregate resource usage into a time-series
and summary metrics.

**Per-sample snapshot (`ResourceSnapshot`):**
```
timestamp, cpu_percent, memory_used_mb, memory_percent,
io_read_bytes, io_write_bytes, io_read_ops, io_write_ops,
net_bytes_sent, net_bytes_recv,
cpu_throttled_periods, cpu_throttled_time_us, memory_oom_events
```

**Aggregated metrics (`SimulationMetrics`):**
```
duration_seconds, exit_code,
peak_cpu_percent, avg_cpu_percent, cpu_throttled_periods, cpu_throttled_time_seconds,
peak_memory_mb, peak_memory_percent, avg_memory_mb, oom_kill_count,
total_read_bytes, total_write_bytes, avg_iops, peak_iops,
total_net_sent_bytes, total_net_recv_bytes
```

**Key derived properties:**
- `was_cpu_constrained` → throttled_periods > 0
- `was_memory_constrained` → oom_kill_count > 0 or peak_memory% > 90
- `workload_succeeded` → exit_code == 0 and oom_kill_count == 0

### 3.7 SDK Compatibility Layer (`sdk_compat/compute_client.py`)

**Purpose:** Provide a drop-in replacement for
`azure.mgmt.compute.ComputeManagementClient` so existing Azure SDK
code works against the digital twin without modification.

**Target SDK:** `azure-mgmt-compute >= 30.0.0`

**Compatible operations:**

| Real Azure SDK call | Digital twin implementation |
|---|---|
| `ComputeManagementClient(credential, sub_id)` | `DigitalTwinComputeManagementClient(credential=None)` |
| `client.virtual_machine_sizes.list(loc)` | Iterates E-series catalog, yields `_VirtualMachineSize` |
| `client.virtual_machines.begin_create_or_update(rg, name, params)` | Creates VM + starts sandbox, returns `_LROPoller` |
| `client.virtual_machines.get(rg, name)` | Returns `VMInstance` |
| `client.virtual_machines.begin_start(rg, name)` | Calls `manager.start()` → creates cgroup |
| `client.virtual_machines.begin_deallocate(rg, name)` | Calls `manager.deallocate()` → destroys cgroup |
| `client.virtual_machines.begin_delete(rg, name)` | Calls `manager.delete()` |
| `client.virtual_machines.list(rg)` | Filters by resource group |
| `client.virtual_machines.instance_view(rg, name)` | Returns power state + provisioning state |

**Parameter compatibility:** Accepts both Python SDK format
(`hardware_profile.vm_size`) and ARM format
(`properties.hardwareProfile.vmSize`).

**LROPoller:** Operations return an `_LROPoller` stub with `.result()`,
`.wait()`, `.done()`, and `.status()` methods.  Since the digital twin
completes synchronously, `.done()` always returns `True`.

## 4. Data Flow

### 4.1 Workload simulation (end-to-end)

```
User code                     Digital Twin                         Linux Kernel
─────────                     ────────────                         ────────────
twin.create_vm("db",          → catalog.get_by_name(sku)
  "Standard_E32s_v5")         → VMInstance(name, vm_size, STOPPED)

twin.start_vm("db")           → governor.create_sandbox(
                                   cpu=32, mem=256GB, iops=51200)
                               → mkdir /sys/fs/cgroup/azure-dt-db
                               → write cpu.max: 3200000 100000    → CFS bandwidth ctrl
                               → write memory.max: 274877906944   → memcg hard limit
                               → write memory.swap.max: 0         → no swap
                               → write io.max: 8:0 riops=51200    → blkio throttle
                               → tc qdisc add rate 16000mbit      → tbf shaping
                               → VMInstance.state = RUNNING

twin.run_workload("db",        → Popen(["sysbench", ...])
  ["sysbench", "memory",       → write PID to cgroup.procs        → process constrained
   "run"])                      → start MetricsCollector thread
                                   ├── sample cpu.stat             → throttled_periods
                                   ├── sample memory.current       → RSS usage
                                   ├── sample memory.events        → oom_kill count
                                   └── sample io.stat              → IOPS counters
                               → proc.communicate()                → wait for exit
                               → aggregate → SimulationMetrics
                               → WorkloadResult(passed/failed)

twin.generate_report("db")    → format metrics into readable text

twin.stop_vm("db")            → rmdir cgroup
                               → tc qdisc del
                               → VMInstance.state = STOPPED
```

### 4.2 SDK-compatible path

```
# This code works with BOTH the real Azure SDK and the digital twin
client = DigitalTwinComputeManagementClient()  # or ComputeManagementClient(cred, sub)

poller = client.virtual_machines.begin_create_or_update(
    "prod-rg", "my-vm",
    {"hardware_profile": {"vm_size": "Standard_E32s_v5"}}
)
vm = poller.result()
# → Real SDK: provisions a VM in Azure
# → Digital twin: creates a cgroup sandbox locally
```

## 5. Models

### 5.1 Specification models (frozen, hashable)

```
VMSize
  ├── name: str                      "Standard_E32s_v5"
  ├── number_of_cores: int           32
  ├── memory_in_mb: int              262144
  ├── series: str                    "Esv5"
  ├── processor: str                 "Intel Xeon Platinum 8473C"
  ├── architecture: ProcessorArchitecture   X86_64
  ├── storage: StorageCapability
  │     ├── max_data_disk_count: int        32
  │     ├── max_iops: int                   51200
  │     ├── max_throughput_mbps: int        865
  │     ├── has_temp_disk: bool             False
  │     ├── premium_io_supported: bool      True
  │     └── ultra_ssd_supported: bool       True
  └── network: NetworkCapability
        ├── max_nics: int                   8
        ├── expected_bandwidth_mbps: int    16000
        └── accelerated_networking: bool    True
```

### 5.2 Runtime models (mutable)

```
VMInstance
  ├── name, vm_size, location, resource_group
  ├── power_state: VMPowerState      RUNNING / STOPPED / DEALLOCATED
  ├── provisioning_state             SUCCEEDED / CREATING / FAILED
  ├── cgroup_path: str               "/sys/fs/cgroup/azure-dt-db"
  └── workload_results: list[WorkloadResult]

WorkloadResult
  ├── vm_instance_name, vm_size, command
  ├── metrics: SimulationMetrics
  │     ├── duration_seconds, exit_code
  │     ├── peak_cpu_percent, avg_cpu_percent
  │     ├── cpu_throttled_periods, cpu_throttled_time_seconds
  │     ├── peak_memory_mb, peak_memory_percent, oom_kill_count
  │     ├── total_read/write_bytes, avg_iops, peak_iops
  │     └── snapshots: list[ResourceSnapshot]   (time-series)
  ├── stdout, stderr
  ├── enforced_constraints: dict
  ├── passed: bool   (exit_code==0 and oom_kill_count==0)
  └── summary() → str

AppliedConstraints
  ├── cpu_cores, cpu_quota_us, cpu_period_us
  ├── memory_limit_bytes
  ├── io_max_iops, io_max_bps
  ├── net_rate_mbit
  ├── cgroup_path
  └── method: "cgroupv2" | "process"
```

## 6. Enforcement Fallback Strategy

The engine is designed to work everywhere — bare metal, VMs,
containers, CI runners — with graceful degradation:

| Environment | CPU | Memory | I/O | Network | Metrics |
|---|---|---|---|---|---|
| Root + cgroup v2 | cpu.max | memory.max | io.max | tc tbf | Full (cgroup stats) |
| Root, no cgroup v2 | sched_setaffinity | RLIMIT_AS | — | tc tbf | Partial (psutil only) |
| Non-root | sched_setaffinity | RLIMIT_AS | — | — | Partial (psutil only) |
| Container | sched_setaffinity | RLIMIT_AS | — | — | Partial (psutil only) |

The `AppliedConstraints.method` field records which level was used, so
reports clearly indicate the enforcement fidelity.

## 7. Test Strategy

**81 tests** across 4 modules:

| Module | Tests | Covers |
|---|---|---|
| `test_e_series_specs.py` | 15 | Catalog queries, filters, data accuracy, memory-to-core ratio |
| `test_digital_twin.py` | 26 | VM lifecycle, workload execution, timeout handling, metrics, reports |
| `test_sdk_compat.py` | 22 | SDK patterns, LROPoller, create/start/stop/delete, resource groups |
| `test_simulator.py` | 18 | ResourceGovernor, NetworkGovernor, VMInstanceManager, sandbox lifecycle |

Tests run without root and without cgroup v2 — they exercise the
process-level fallback path.  The cgroup v2 path is tested on Linux
hosts with elevated privileges.

## 8. File Layout

```
src/azure_vm_digital_twin/
├── __init__.py                      Public API exports
├── models.py                        All data models (specs + runtime)
├── e_series_specs.py                E-series catalog (63 SKUs)
├── digital_twin.py                  Top-level orchestrator
├── simulator/
│   ├── resource_governor.py         cgroup v2 / process-level enforcement
│   ├── network_governor.py          tc-based bandwidth shaping
│   └── vm_instance.py               VM lifecycle state machine
├── workload/
│   ├── runner.py                    Workload execution engine
│   └── metrics.py                   Metrics sampling and aggregation
└── sdk_compat/
    └── compute_client.py            azure-mgmt-compute compatible client
```
