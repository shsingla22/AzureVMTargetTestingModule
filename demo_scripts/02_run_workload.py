"""Demo: Run a real workload inside a digital-twin VM's resource constraints."""
import sys; sys.path.insert(0, "src")

from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()
twin.create_vm("compute-test", "Standard_E4s_v5")
twin.start_vm("compute-test")

# Run a CPU-intensive workload constrained to E4s_v5 limits (4 vCPUs, 32 GB)
result = twin.run_workload(
    "compute-test",
    ["python3", "-c", "import math; [math.factorial(5000) for _ in range(200)]"],
)
print(result.summary())

twin.cleanup()
