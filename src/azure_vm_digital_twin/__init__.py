"""Azure VM Digital Twin - E-Series VM compatibility validation for on-premises migration."""

from azure_vm_digital_twin.models import (
    VMSize,
    OnPremVMProfile,
    CompatibilityResult,
    CompatibilityStatus,
)
from azure_vm_digital_twin.e_series_specs import ESeriesCatalog
from azure_vm_digital_twin.digital_twin import AzureESeriesDigitalTwin

__version__ = "0.1.0"
__all__ = [
    "VMSize",
    "OnPremVMProfile",
    "CompatibilityResult",
    "CompatibilityStatus",
    "ESeriesCatalog",
    "AzureESeriesDigitalTwin",
]
