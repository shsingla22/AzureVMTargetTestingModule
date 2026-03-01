"""Metrics collector that samples resource usage during workload execution.

Reads from cgroup stats when available, otherwise falls back to psutil
for process-level metrics.  Produces ResourceSnapshot time-series that
are aggregated into SimulationMetrics.
"""

from __future__ import annotations

import time
from typing import Optional

import psutil

from azure_vm_digital_twin.models import ResourceSnapshot, SimulationMetrics
from azure_vm_digital_twin.simulator.resource_governor import ResourceGovernor


class MetricsCollector:
    """Collects resource-usage snapshots for a running workload process."""

    def __init__(
        self,
        governor: ResourceGovernor,
        sandbox_name: str,
        pid: int,
        memory_limit_mb: int,
    ) -> None:
        self._governor = governor
        self._sandbox_name = sandbox_name
        self._pid = pid
        self._memory_limit_mb = memory_limit_mb
        self._snapshots: list[ResourceSnapshot] = []
        self._start_time = time.monotonic()
        self._prev_io: Optional[dict] = None
        self._prev_time: Optional[float] = None

    def sample(self) -> Optional[ResourceSnapshot]:
        """Take a single resource-usage snapshot."""
        now = time.monotonic()
        snap = ResourceSnapshot(timestamp=now - self._start_time)

        # Process-level metrics via psutil
        try:
            proc = psutil.Process(self._pid)
            snap.cpu_percent = proc.cpu_percent(interval=0)
            mem_info = proc.memory_info()
            snap.memory_used_mb = mem_info.rss / (1024 * 1024)
            if self._memory_limit_mb > 0:
                snap.memory_percent = (
                    snap.memory_used_mb / self._memory_limit_mb * 100.0
                )

            io = proc.io_counters()
            snap.io_read_bytes = io.read_bytes
            snap.io_write_bytes = io.write_bytes
            snap.io_read_ops = io.read_count
            snap.io_write_ops = io.write_count
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        # Cgroup-level stats (more accurate when available)
        cpu_stats = self._governor.read_cpu_stats(self._sandbox_name)
        snap.cpu_throttled_periods = cpu_stats.get("throttled_periods", 0)
        snap.cpu_throttled_time_us = cpu_stats.get("throttled_time_us", 0)

        mem_stats = self._governor.read_memory_stats(self._sandbox_name)
        if mem_stats.get("current_bytes", 0) > 0:
            snap.memory_used_mb = mem_stats["current_bytes"] / (1024 * 1024)
            if self._memory_limit_mb > 0:
                snap.memory_percent = (
                    snap.memory_used_mb / self._memory_limit_mb * 100.0
                )
        snap.memory_oom_events = mem_stats.get("oom_kill", 0)

        io_stats = self._governor.read_io_stats(self._sandbox_name)
        if io_stats.get("rbytes", 0) > 0 or io_stats.get("wbytes", 0) > 0:
            snap.io_read_bytes = io_stats["rbytes"]
            snap.io_write_bytes = io_stats["wbytes"]
            snap.io_read_ops = io_stats["rios"]
            snap.io_write_ops = io_stats["wios"]

        self._snapshots.append(snap)
        return snap

    def aggregate(self, exit_code: int, vm_size_name: str) -> SimulationMetrics:
        """Aggregate all snapshots into final SimulationMetrics."""
        duration = time.monotonic() - self._start_time
        metrics = SimulationMetrics(
            vm_size_name=vm_size_name,
            duration_seconds=duration,
            exit_code=exit_code,
            snapshots=list(self._snapshots),
        )

        if not self._snapshots:
            return metrics

        # CPU aggregation
        cpu_values = [s.cpu_percent for s in self._snapshots]
        metrics.peak_cpu_percent = max(cpu_values) if cpu_values else 0.0
        metrics.avg_cpu_percent = (
            sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        )
        last = self._snapshots[-1]
        metrics.cpu_throttled_periods = last.cpu_throttled_periods
        metrics.cpu_throttled_time_seconds = last.cpu_throttled_time_us / 1_000_000

        # Memory aggregation
        mem_values = [s.memory_used_mb for s in self._snapshots]
        metrics.peak_memory_mb = max(mem_values) if mem_values else 0.0
        metrics.avg_memory_mb = (
            sum(mem_values) / len(mem_values) if mem_values else 0.0
        )
        if self._memory_limit_mb > 0:
            metrics.peak_memory_percent = (
                metrics.peak_memory_mb / self._memory_limit_mb * 100.0
            )
        metrics.oom_kill_count = max(
            s.memory_oom_events for s in self._snapshots
        )

        # I/O aggregation
        metrics.total_read_bytes = last.io_read_bytes
        metrics.total_write_bytes = last.io_write_bytes
        metrics.total_read_ops = last.io_read_ops
        metrics.total_write_ops = last.io_write_ops
        if duration > 0:
            total_ops = metrics.total_read_ops + metrics.total_write_ops
            metrics.avg_iops = total_ops / duration

        # Per-interval IOPS for peak
        if len(self._snapshots) >= 2:
            iops_values = []
            for i in range(1, len(self._snapshots)):
                prev = self._snapshots[i - 1]
                curr = self._snapshots[i]
                dt = curr.timestamp - prev.timestamp
                if dt > 0:
                    ops = (
                        (curr.io_read_ops - prev.io_read_ops)
                        + (curr.io_write_ops - prev.io_write_ops)
                    )
                    iops_values.append(ops / dt)
            metrics.peak_iops = max(iops_values) if iops_values else 0.0

        # Network
        metrics.total_net_sent_bytes = last.net_bytes_sent
        metrics.total_net_recv_bytes = last.net_bytes_recv

        return metrics
