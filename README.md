# Azure E-Series VM Digital Twin

A simulation engine that creates digital twins of Azure E-series
(memory-optimized) virtual machines.  It enforces real resource
constraints — CPU cores, memory, IOPS, network bandwidth — via Linux
cgroups so you can run actual customer workloads inside them and
observe how they behave **before** committing to a migration.

## Quick start

```python
from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()

# Create a VM pinned to Standard_E16s_v5 (16 vCPUs, 128 GB)
twin.create_vm("db-test", "Standard_E16s_v5")
twin.start_vm("db-test")            # enforces cgroup constraints

# Run your workload under those constraints
result = twin.run_workload("db-test", ["sysbench", "memory", "run"])

if result.passed:
    print("Workload is viable on Standard_E16s_v5")
else:
    print(f"OOM kills: {result.metrics.oom_kill_count}")
    print(f"CPU throttled: {result.metrics.cpu_throttled_periods} periods")

twin.stop_vm("db-test")
```

## SDK compatibility

The digital twin exposes the same interface as
`azure.mgmt.compute.ComputeManagementClient`, so code written against
the real Azure SDK works unchanged:

```python
from azure_vm_digital_twin.sdk_compat import DigitalTwinComputeManagementClient

# Drop-in replacement — no Azure credentials needed
client = DigitalTwinComputeManagementClient(credential=None)

# Same API as the real SDK
poller = client.virtual_machines.begin_create_or_update(
    "my-rg", "test-vm",
    {"hardware_profile": {"vm_size": "Standard_E32s_v5"}},
)
vm = poller.result()

for size in client.virtual_machine_sizes.list("eastus"):
    print(size.name, size.number_of_cores, size.memory_in_mb)
```

## Installation

```bash
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v
```

## VM catalog

63 E-series sizes across 8 sub-series:

| Sub-series | Processor | Sizes | vCPU range | Memory range |
|------------|-----------|-------|------------|--------------|
| Esv5 | Intel Sapphire Rapids | 10 | 2–104 | 16–672 GB |
| Edsv5 | Intel Ice Lake (+ temp disk) | 8 | 2–96 | 16–672 GB |
| Easv5 | AMD EPYC Milan | 8 | 2–96 | 16–672 GB |
| Eadsv5 | AMD EPYC Milan (+ temp disk) | 7 | 2–96 | 16–672 GB |
| Easv6 | AMD EPYC Genoa | 8 | 2–96 | 16–672 GB |
| Epsv5 | Ampere Altra (ARM64) | 5 | 2–32 | 16–208 GB |
| Epsv6 | Azure Cobalt 100 (ARM64) | 8 | 2–96 | 16–672 GB |
| Esv7 | Intel Granite Rapids | 9 | 2–128 | 16–1024 GB |

See [DESIGN.md](DESIGN.md) for the full architecture.
