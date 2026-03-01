"""SDK compatibility demo - drop-in replacement for azure-mgmt-compute."""
import sys
sys.path.insert(0, "src")

from azure_vm_digital_twin.sdk_compat import DigitalTwinComputeManagementClient

# Same pattern as: ComputeManagementClient(credential, subscription_id)
client = DigitalTwinComputeManagementClient(
    credential=None,  # No Azure credentials needed
    subscription_id="digital-twin",
)

# Same pattern as: client.virtual_machine_sizes.list(location)
print("Listing VM sizes (azure-mgmt-compute compatible interface):")
print("-" * 72)
count = 0
for size in client.virtual_machine_sizes.list("eastus"):
    d = size.as_dict()
    name = d["name"]
    cores = d["number_of_cores"]
    mem = d["memory_in_mb"]
    disks = d["max_data_disk_count"]
    print(f"  {name:<30s}  {cores:>3d} cores  {mem:>7d} MB  disks={disks}")
    count += 1
    if count >= 10:
        remaining = 63 - count
        print(f"  ... and {remaining} more sizes")
        break
