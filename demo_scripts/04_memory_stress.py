"""Demo: Memory stress test — see how workload behaves under E-series memory limits."""
import sys; sys.path.insert(0, "src")

from azure_vm_digital_twin import AzureESeriesDigitalTwin

twin = AzureESeriesDigitalTwin()

# Small VM: 2 vCPUs, 16 GB RAM
twin.create_vm("mem-test", "Standard_E2s_v5")
twin.start_vm("mem-test")

# Allocate ~50 MB of memory — well within limits
result = twin.run_workload(
    "mem-test",
    ["python3", "-c", "data = bytearray(50 * 1024 * 1024); print(f'Allocated {len(data) // (1024*1024)} MB')"],
)
print(f"50 MB allocation: {'PASSED' if result.passed else 'FAILED'}")
print(f"  Peak memory: {result.metrics.peak_memory_mb:.1f} MB")
print(f"  OOM kills:   {result.metrics.oom_kill_count}")
print()

# Full report
print(twin.generate_report("mem-test"))

twin.cleanup()
