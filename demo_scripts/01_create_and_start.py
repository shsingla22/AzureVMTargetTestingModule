"""Demo: Create a digital-twin VM and enforce E-series resource constraints."""
import sys; sys.path.insert(0, "src")

from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()

# Create a VM pinned to Standard_E8s_v5 (8 vCPUs, 64 GB RAM)
vm = twin.create_vm("db-test-01", "Standard_E8s_v5")
print(f"Created VM: {vm.name}")
print(f"  SKU:      {vm.vm_size.name}")
print(f"  vCPUs:    {vm.vm_size.number_of_cores}")
print(f"  Memory:   {vm.vm_size.memory_in_mb // 1024} GB")
print(f"  Max IOPS: {vm.vm_size.storage.max_iops}")
print(f"  State:    {vm.power_state.value}")
print()

# Start the VM — this creates the cgroup sandbox and enforces limits
constraints = twin.start_vm("db-test-01")
print(f"Started VM — enforcement method: {constraints.method}")
print(f"  CPU limit:    {constraints.cpu_cores} cores")
print(f"  Memory limit: {constraints.memory_limit_bytes // (1024**3)} GB")
if constraints.io_max_iops:
    print(f"  IOPS limit:   {constraints.io_max_iops}")
print(f"  State:        {twin.get_vm('db-test-01').power_state.value}")

twin.cleanup()
