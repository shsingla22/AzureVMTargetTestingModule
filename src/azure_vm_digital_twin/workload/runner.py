"""Workload runner that executes commands inside a digital-twin VM's
resource sandbox and collects performance metrics.

The runner:
1. Spawns the workload process
2. Moves it into the VM's cgroup (or applies process-level limits)
3. Polls resource usage at configurable intervals
4. Returns a WorkloadResult with full metrics

This is the core of the digital twin: it lets you answer "how will my
workload actually behave on a Standard_E16s_v5?" by running it under
that SKU's exact resource constraints.
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Optional

from azure_vm_digital_twin.models import (
    VMInstance,
    VMPowerState,
    WorkloadResult,
)
from azure_vm_digital_twin.simulator.vm_instance import VMInstanceManager
from azure_vm_digital_twin.workload.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class WorkloadRunner:
    """Execute workloads inside digital-twin VM sandboxes.

    Usage::

        mgr = VMInstanceManager()
        mgr.create("db-test", "Standard_E32s_v5")
        mgr.start("db-test")

        runner = WorkloadRunner(mgr)
        result = runner.run("db-test", ["sysbench", "memory", "run"])
        print(result.summary())

        mgr.stop("db-test")
    """

    def __init__(
        self,
        instance_manager: VMInstanceManager,
        sample_interval: float = 0.5,
    ) -> None:
        self._mgr = instance_manager
        self._sample_interval = sample_interval

    def run(
        self,
        vm_name: str,
        command: list[str],
        timeout: Optional[float] = None,
        env: Optional[dict] = None,
        cwd: Optional[str] = None,
        capture_output: bool = True,
    ) -> WorkloadResult:
        """Run a command inside a VM's resource sandbox.

        Args:
            vm_name: Name of the digital-twin VM (must be started).
            command: Command and arguments to execute.
            timeout: Maximum seconds to run (None = unlimited).
            env: Extra environment variables for the process.
            cwd: Working directory for the process.
            capture_output: If True, capture stdout/stderr.

        Returns:
            WorkloadResult with metrics, output, and pass/fail verdict.
        """
        vm = self._mgr.get(vm_name)
        if vm is None:
            raise ValueError(f"VM '{vm_name}' does not exist")
        if not vm.is_running:
            raise RuntimeError(
                f"VM '{vm_name}' is not running "
                f"(state={vm.power_state.value}). Call start() first."
            )

        governor = self._mgr.governor
        constraints = governor.get_constraints(vm_name)

        logger.info("Running workload in VM '%s': %s", vm_name, command)

        # Spawn the process
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            env=env,
            cwd=cwd,
        )

        # Move into cgroup sandbox
        try:
            governor.apply_to_pid(vm_name, proc.pid)
        except Exception as e:
            logger.warning("Could not apply sandbox to PID %d: %s", proc.pid, e)

        # Start metrics collection in a background thread
        collector = MetricsCollector(
            governor=governor,
            sandbox_name=vm_name,
            pid=proc.pid,
            memory_limit_mb=vm.vm_size.memory_in_mb,
        )
        stop_event = threading.Event()
        collector_thread = threading.Thread(
            target=self._collect_loop,
            args=(collector, stop_event),
            daemon=True,
        )
        collector_thread.start()

        # Wait for completion
        stdout_bytes = b""
        stderr_bytes = b""
        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_bytes, stderr_bytes = proc.communicate()
            logger.warning("Workload timed out after %s seconds", timeout)

        # Stop collection
        stop_event.set()
        collector_thread.join(timeout=5.0)

        # Take a final sample
        try:
            collector.sample()
        except Exception:
            pass

        # Build result
        metrics = collector.aggregate(
            exit_code=proc.returncode,
            vm_size_name=vm.vm_size.name,
        )

        enforced = constraints.as_dict() if constraints else {}

        result = WorkloadResult(
            vm_instance_name=vm_name,
            vm_size=vm.vm_size,
            command=command,
            metrics=metrics,
            stdout=(stdout_bytes or b"").decode("utf-8", errors="replace"),
            stderr=(stderr_bytes or b"").decode("utf-8", errors="replace"),
            enforced_constraints=enforced,
        )

        vm.workload_results.append(result)
        return result

    def run_script(
        self,
        vm_name: str,
        script: str,
        interpreter: str = "bash",
        timeout: Optional[float] = None,
    ) -> WorkloadResult:
        """Run a shell script inside a VM's resource sandbox.

        Convenience wrapper that writes a script string and executes it.
        """
        return self.run(
            vm_name=vm_name,
            command=[interpreter, "-c", script],
            timeout=timeout,
        )

    def _collect_loop(
        self,
        collector: MetricsCollector,
        stop_event: threading.Event,
    ) -> None:
        """Background loop that samples metrics at regular intervals."""
        while not stop_event.is_set():
            try:
                collector.sample()
            except Exception as e:
                logger.debug("Metrics sample failed: %s", e)
            stop_event.wait(self._sample_interval)
