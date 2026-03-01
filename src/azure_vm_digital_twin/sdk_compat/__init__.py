"""SDK compatibility layer mirroring azure-mgmt-compute client interfaces."""

from azure_vm_digital_twin.sdk_compat.compute_client import (
    DigitalTwinComputeManagementClient,
    VirtualMachineSizesOperations,
)

__all__ = [
    "DigitalTwinComputeManagementClient",
    "VirtualMachineSizesOperations",
]
