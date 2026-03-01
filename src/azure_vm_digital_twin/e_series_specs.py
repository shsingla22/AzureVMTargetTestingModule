"""Comprehensive catalog of Azure E-series VM family specifications.

Data sourced from Microsoft Azure documentation:
https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/memory-optimized/e-family

Each entry mirrors the azure-mgmt-compute VirtualMachineSize fields plus
extended attributes used by the digital twin compatibility engine.
"""

from __future__ import annotations

from typing import Iterator, Optional

from azure_vm_digital_twin.models import (
    NetworkCapability,
    ProcessorArchitecture,
    StorageCapability,
    VMSize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gb_to_mb(gb: int) -> int:
    return gb * 1024


# ---------------------------------------------------------------------------
# Esv5 series  (Intel Sapphire Rapids / Ice Lake / Emerald Rapids, no temp disk)
# ---------------------------------------------------------------------------

_ESV5_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2s_v5", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=3750, max_throughput_mbps=85, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4s_v5", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=145, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8s_v5", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=290, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16s_v5", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=580, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E20s_v5", number_of_cores=20, memory_in_mb=_gb_to_mb(160),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=32000, max_throughput_mbps=750, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32s_v5", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=865, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E48s_v5", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=76800, max_throughput_mbps=1315, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=24000),
    ),
    VMSize(
        name="Standard_E64s_v5", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=80000, max_throughput_mbps=2000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=30000),
    ),
    VMSize(
        name="Standard_E96s_v5", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=120000, max_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=100000),
    ),
    VMSize(
        name="Standard_E104s_v5", number_of_cores=104, memory_in_mb=_gb_to_mb(672),
        series="Esv5",
        processor="Intel Xeon Platinum 8473C (Sapphire Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=120000, max_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=100000),
    ),
]

# ---------------------------------------------------------------------------
# Edsv5 series  (Intel, with temp SSD)
# ---------------------------------------------------------------------------

_EDSV5_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2ds_v5", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=3750, max_throughput_mbps=85, has_temp_disk=True, temp_disk_size_gb=75, temp_disk_iops=9000, temp_disk_throughput_mbps=125, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4ds_v5", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=145, has_temp_disk=True, temp_disk_size_gb=150, temp_disk_iops=19000, temp_disk_throughput_mbps=250, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8ds_v5", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=290, has_temp_disk=True, temp_disk_size_gb=300, temp_disk_iops=38000, temp_disk_throughput_mbps=500, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16ds_v5", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=580, has_temp_disk=True, temp_disk_size_gb=600, temp_disk_iops=75000, temp_disk_throughput_mbps=1000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32ds_v5", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=865, has_temp_disk=True, temp_disk_size_gb=1200, temp_disk_iops=150000, temp_disk_throughput_mbps=2000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E48ds_v5", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=76800, max_throughput_mbps=1315, has_temp_disk=True, temp_disk_size_gb=1800, temp_disk_iops=225000, temp_disk_throughput_mbps=3000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=24000),
    ),
    VMSize(
        name="Standard_E64ds_v5", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=80000, max_throughput_mbps=2000, has_temp_disk=True, temp_disk_size_gb=2400, temp_disk_iops=300000, temp_disk_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=30000),
    ),
    VMSize(
        name="Standard_E96ds_v5", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Edsv5",
        processor="Intel Xeon Platinum 8370C (Ice Lake)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=120000, max_throughput_mbps=4000, has_temp_disk=True, temp_disk_size_gb=3600, temp_disk_iops=450000, temp_disk_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=100000),
    ),
]

# ---------------------------------------------------------------------------
# Easv5 series  (AMD EPYC Milan / Genoa, no temp disk)
# ---------------------------------------------------------------------------

_EASV5_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2as_v5", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=3750, max_throughput_mbps=82, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4as_v5", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=144, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8as_v5", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=200, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16as_v5", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=384, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32as_v5", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=768, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E48as_v5", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=76800, max_throughput_mbps=1148, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=24000),
    ),
    VMSize(
        name="Standard_E64as_v5", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=80000, max_throughput_mbps=1200, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=32000),
    ),
    VMSize(
        name="Standard_E96as_v5", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Easv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=120000, max_throughput_mbps=2000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=50000),
    ),
]

# ---------------------------------------------------------------------------
# Eadsv5 series  (AMD, with temp NVMe)
# ---------------------------------------------------------------------------

_EADSV5_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2ads_v5", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=3750, max_throughput_mbps=82, has_temp_disk=True, temp_disk_size_gb=75, temp_disk_iops=9000, temp_disk_throughput_mbps=125, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4ads_v5", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=144, has_temp_disk=True, temp_disk_size_gb=150, temp_disk_iops=19000, temp_disk_throughput_mbps=250, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8ads_v5", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=200, has_temp_disk=True, temp_disk_size_gb=300, temp_disk_iops=38000, temp_disk_throughput_mbps=500, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16ads_v5", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=384, has_temp_disk=True, temp_disk_size_gb=600, temp_disk_iops=75000, temp_disk_throughput_mbps=1000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32ads_v5", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=768, has_temp_disk=True, temp_disk_size_gb=1200, temp_disk_iops=150000, temp_disk_throughput_mbps=2000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E64ads_v5", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=80000, max_throughput_mbps=1200, has_temp_disk=True, temp_disk_size_gb=2400, temp_disk_iops=300000, temp_disk_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=32000),
    ),
    VMSize(
        name="Standard_E96ads_v5", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Eadsv5",
        processor="AMD EPYC 7763v (Milan)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=120000, max_throughput_mbps=2000, has_temp_disk=True, temp_disk_size_gb=3600, temp_disk_iops=450000, temp_disk_throughput_mbps=4000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=50000),
    ),
]

# ---------------------------------------------------------------------------
# Easv6 series  (AMD EPYC Genoa, no temp disk)
# ---------------------------------------------------------------------------

_EASV6_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2as_v6", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=4000, max_throughput_mbps=90, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4as_v6", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=7600, max_throughput_mbps=180, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8as_v6", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=15200, max_throughput_mbps=360, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16as_v6", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=30400, max_throughput_mbps=720, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32as_v6", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=57600, max_throughput_mbps=1440, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E48as_v6", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=86400, max_throughput_mbps=2160, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=24000),
    ),
    VMSize(
        name="Standard_E64as_v6", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=115200, max_throughput_mbps=2880, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=30000),
    ),
    VMSize(
        name="Standard_E96as_v6", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Easv6",
        processor="AMD EPYC 9004 (Genoa)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=175000, max_throughput_mbps=4320, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=40000),
    ),
]

# ---------------------------------------------------------------------------
# Epsv5 series  (Ampere Altra ARM64, no temp disk)
# ---------------------------------------------------------------------------

_EPSV5_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2ps_v5", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Epsv5",
        processor="Ampere Altra",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=4, max_iops=3750, max_throughput_mbps=85, premium_io_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4ps_v5", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Epsv5",
        processor="Ampere Altra",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=145, premium_io_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8ps_v5", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Epsv5",
        processor="Ampere Altra",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=290, premium_io_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16ps_v5", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Epsv5",
        processor="Ampere Altra",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=580, premium_io_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32ps_v5", number_of_cores=32, memory_in_mb=_gb_to_mb(208),
        series="Epsv5",
        processor="Ampere Altra",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=865, premium_io_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
]

# ---------------------------------------------------------------------------
# Epsv6 series  (Azure Cobalt 100 ARM64, no temp disk)
# ---------------------------------------------------------------------------

_EPSV6_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2ps_v6", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=3750, max_throughput_mbps=106, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E4ps_v6", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=8, max_iops=6400, max_throughput_mbps=212, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=2, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E8ps_v6", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=12800, max_throughput_mbps=424, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E16ps_v6", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=25600, max_throughput_mbps=848, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=12500),
    ),
    VMSize(
        name="Standard_E32ps_v6", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=51200, max_throughput_mbps=1696, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E48ps_v6", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=76800, max_throughput_mbps=2544, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=24000),
    ),
    VMSize(
        name="Standard_E64ps_v6", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=102400, max_throughput_mbps=3392, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=30000),
    ),
    VMSize(
        name="Standard_E96ps_v6", number_of_cores=96, memory_in_mb=_gb_to_mb(672),
        series="Epsv6",
        processor="Azure Cobalt 100",
        architecture=ProcessorArchitecture.ARM64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=153600, max_throughput_mbps=5000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=60000),
    ),
]

# ---------------------------------------------------------------------------
# Esv7 series  (Intel Granite Rapids, latest gen, no temp disk)
# ---------------------------------------------------------------------------

_ESV7_SIZES: list[VMSize] = [
    VMSize(
        name="Standard_E2s_v7", number_of_cores=2, memory_in_mb=_gb_to_mb(16),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=10, max_iops=4000, max_throughput_mbps=115, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=3, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E4s_v7", number_of_cores=4, memory_in_mb=_gb_to_mb(32),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=10, max_iops=8000, max_throughput_mbps=230, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=3, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E8s_v7", number_of_cores=8, memory_in_mb=_gb_to_mb(64),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=16, max_iops=16000, max_throughput_mbps=460, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=4, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E16s_v7", number_of_cores=16, memory_in_mb=_gb_to_mb(128),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=32000, max_throughput_mbps=920, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=16000),
    ),
    VMSize(
        name="Standard_E32s_v7", number_of_cores=32, memory_in_mb=_gb_to_mb(256),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=64000, max_throughput_mbps=1840, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=20000),
    ),
    VMSize(
        name="Standard_E48s_v7", number_of_cores=48, memory_in_mb=_gb_to_mb(384),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=32, max_iops=96000, max_throughput_mbps=2760, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=25000),
    ),
    VMSize(
        name="Standard_E64s_v7", number_of_cores=64, memory_in_mb=_gb_to_mb(512),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=128000, max_throughput_mbps=3680, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=30000),
    ),
    VMSize(
        name="Standard_E96s_v7", number_of_cores=96, memory_in_mb=_gb_to_mb(768),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=192000, max_throughput_mbps=5520, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=40000),
    ),
    VMSize(
        name="Standard_E128s_v7", number_of_cores=128, memory_in_mb=_gb_to_mb(1024),
        series="Esv7",
        processor="Intel Xeon 6 6973P-C (Granite Rapids)",
        architecture=ProcessorArchitecture.X86_64,
        storage=StorageCapability(max_data_disk_count=64, max_iops=250000, max_throughput_mbps=8000, premium_io_supported=True, ultra_ssd_supported=True),
        network=NetworkCapability(max_nics=8, expected_bandwidth_mbps=50000),
    ),
]

# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

_ALL_SERIES: dict[str, list[VMSize]] = {
    "Esv5": _ESV5_SIZES,
    "Edsv5": _EDSV5_SIZES,
    "Easv5": _EASV5_SIZES,
    "Eadsv5": _EADSV5_SIZES,
    "Easv6": _EASV6_SIZES,
    "Epsv5": _EPSV5_SIZES,
    "Epsv6": _EPSV6_SIZES,
    "Esv7": _ESV7_SIZES,
}


class ESeriesCatalog:
    """Queryable catalog of all Azure E-series VM sizes.

    Provides an API compatible with ``azure.mgmt.compute`` list operations
    so users can swap the digital twin in place of a live Azure client.
    """

    def __init__(self, series_filter: Optional[list[str]] = None) -> None:
        if series_filter:
            self._sizes = {k: v for k, v in _ALL_SERIES.items() if k in series_filter}
        else:
            self._sizes = dict(_ALL_SERIES)

    # -- azure-mgmt-compute compatible iteration ----------------------------

    def list(self) -> Iterator[VMSize]:
        """Iterate over all VM sizes (mirrors ``virtual_machine_sizes.list()``)."""
        for sizes in self._sizes.values():
            yield from sizes

    # -- convenience queries ------------------------------------------------

    @property
    def series_names(self) -> list[str]:
        return list(self._sizes.keys())

    def get_by_name(self, name: str) -> Optional[VMSize]:
        for vm in self.list():
            if vm.name == name:
                return vm
        return None

    def get_series(self, series: str) -> list[VMSize]:
        return list(self._sizes.get(series, []))

    def filter_by_cores(self, min_cores: int, max_cores: Optional[int] = None) -> list[VMSize]:
        result = [vm for vm in self.list() if vm.number_of_cores >= min_cores]
        if max_cores is not None:
            result = [vm for vm in result if vm.number_of_cores <= max_cores]
        return result

    def filter_by_memory_gb(self, min_gb: int, max_gb: Optional[int] = None) -> list[VMSize]:
        min_mb = min_gb * 1024
        result = [vm for vm in self.list() if vm.memory_in_mb >= min_mb]
        if max_gb is not None:
            max_mb = max_gb * 1024
            result = [vm for vm in result if vm.memory_in_mb <= max_mb]
        return result

    def filter_by_architecture(self, arch: ProcessorArchitecture) -> list[VMSize]:
        return [vm for vm in self.list() if vm.architecture == arch]

    def count(self) -> int:
        return sum(len(v) for v in self._sizes.values())
