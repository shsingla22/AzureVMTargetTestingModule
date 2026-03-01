"""Demo: Use azure-mgmt-compute compatible SDK to manage digital-twin VMs."""
import sys; sys.path.insert(0, "src")

from azure_vm_digital_twin.sdk_compat import DigitalTwinComputeManagementClient

# Same interface as: ComputeManagementClient(credential, subscription_id)
client = DigitalTwinComputeManagementClient(
    credential=None,
    subscription_id="digital-twin",
)

# Pattern: client.virtual_machines.begin_create_or_update(rg, name, params)
print("Creating VM via SDK-compatible interface...")
poller = client.virtual_machines.begin_create_or_update(
    "prod-rg", "web-server",
    {"hardware_profile": {"vm_size": "Standard_E16s_v5"}},
)
vm = poller.result()
print(f"  Created: {vm.name} ({vm.vm_size.name}, {vm.vm_size.number_of_cores} vCPUs)")
print(f"  State:   {vm.power_state.value}")

# Pattern: client.virtual_machines.instance_view(rg, name)
view = client.virtual_machines.instance_view("prod-rg", "web-server")
print(f"  Instance view: {[s['code'] for s in view['statuses']]}")

# Pattern: client.virtual_machines.begin_deallocate(rg, name)
print("\nDeallocating VM...")
client.virtual_machines.begin_deallocate("prod-rg", "web-server").wait()
vm = client.virtual_machines.get("prod-rg", "web-server")
print(f"  State: {vm.power_state.value}")

# Pattern: client.virtual_machines.begin_start(rg, name)
print("\nRestarting VM...")
client.virtual_machines.begin_start("prod-rg", "web-server").wait()
vm = client.virtual_machines.get("prod-rg", "web-server")
print(f"  State: {vm.power_state.value}")

# Pattern: client.virtual_machines.list(rg)
print("\nListing VMs in resource group:")
for v in client.virtual_machines.list("prod-rg"):
    print(f"  {v.name}: {v.vm_size.name} [{v.power_state.value}]")

# Cleanup
client.virtual_machines.begin_delete("prod-rg", "web-server").wait()
print("\nVM deleted.")
client.close()
