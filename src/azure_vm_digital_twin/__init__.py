"""Azure VM Digital Twin - E-Series VM simulation engine.

Simulates Azure E-series VM resource constraints (CPU, memory, IOPS,
network bandwidth) via Linux cgroups so real customer workloads can be
tested against target SKUs before migration.
"""

from azure_vm_digital_twin.models import (
    VMSize,
    VMInstance,
    VMPowerState,
    SimulationMetrics,
    WorkloadResult,
)
from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.digital_twin import AzureESeriesDigitalTwin

__version__ = "0.1.0"
__all__ = [
    "VMSize",
    "VMInstance",
    "VMPowerState",
    "SimulationMetrics",
    "WorkloadResult",
    "ESeriesCatalog",
    "AzureESeriesDigitalTwin",
]
