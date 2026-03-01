"""Migration compatibility analysis demo."""
import sys
sys.path.insert(0, "src")

from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()

# Simulate a mid-size database server migration
profile = twin.profile_from_specs(
    hostname="oltp-db-prod-01",
    vcpus=32,
    memory_mb=256 * 1024,  # 256 GB
    os_type="Linux",
    data_disks_count=12,
    required_iops=50000,
    required_throughput_mbps=800,
    required_nics=2,
    requires_premium_io=True,
)

recommendation = twin.recommend(profile)
report = twin.generate_report(recommendation)
print(report)
