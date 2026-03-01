"""Single VM size compatibility check demo."""
import sys
sys.path.insert(0, "src")

from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()

# A small web application server
profile = twin.profile_from_specs(
    hostname="web-app-01",
    vcpus=8,
    memory_mb=32 * 1024,
    os_type="Linux",
    data_disks_count=2,
    required_iops=6000,
    required_nics=2,
)

# Check against a specific VM size
result = twin.check_vm_size(profile, "Standard_E8s_v5")
print(result.summary())
print()

# Now check against a size that is too small
result2 = twin.check_vm_size(profile, "Standard_E2s_v5")
print(result2.summary())
