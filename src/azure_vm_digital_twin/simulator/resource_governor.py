"""Resource governor that enforces CPU and memory limits via Linux cgroups v2.

When cgroups v2 is unavailable (e.g. containers, non-root), the governor
falls back to process-level limits using os.sched_setaffinity and
resource.setrlimit.  This lets the digital twin run *everywhere* while
still providing real constraint enforcement where the kernel supports it.
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cgroup v2 unified hierarchy mount point
_CGROUP_ROOT = Path("/sys/fs/cgroup")
_TWIN_PREFIX = "azure-dt"


@dataclass
class AppliedConstraints:
    """Record of which constraints were actually enforced."""
    cpu_cores: Optional[int] = None
    cpu_quota_us: Optional[int] = None
    cpu_period_us: int = 100_000
    memory_limit_bytes: Optional[int] = None
    io_max_iops: Optional[int] = None
    io_max_bps: Optional[int] = None
    net_rate_mbit: Optional[int] = None
    cgroup_path: Optional[str] = None
    method: str = "none"  # "cgroupv2" | "process" | "none"

    def as_dict(self) -> dict:
        d = {}
        if self.cpu_cores is not None:
            d["cpu_cores"] = self.cpu_cores
        if self.cpu_quota_us is not None:
            d["cpu_quota_us"] = f"{self.cpu_quota_us}/{self.cpu_period_us}"
        if self.memory_limit_bytes is not None:
            d["memory_limit_mb"] = self.memory_limit_bytes // (1024 * 1024)
        if self.io_max_iops is not None:
            d["io_max_iops"] = self.io_max_iops
        if self.io_max_bps is not None:
            d["io_max_bps"] = self.io_max_bps
        if self.net_rate_mbit is not None:
            d["net_rate_mbit"] = self.net_rate_mbit
        d["enforcement"] = self.method
        return d


def _cgroup_v2_available() -> bool:
    """Check whether cgroup v2 unified hierarchy is mounted and writable."""
    cgroup_type = _CGROUP_ROOT / "cgroup.type"
    cgroup_controllers = _CGROUP_ROOT / "cgroup.controllers"
    # Unified hierarchy: /sys/fs/cgroup/cgroup.controllers exists
    if not cgroup_controllers.exists():
        return False
    # Check we can create sub-cgroups
    try:
        test_path = _CGROUP_ROOT / f"{_TWIN_PREFIX}-probe"
        test_path.mkdir(exist_ok=True)
        test_path.rmdir()
        return True
    except PermissionError:
        return False
    except OSError:
        return False


class ResourceGovernor:
    """Creates and manages cgroup-based resource sandboxes for digital-twin VMs.

    Usage::

        gov = ResourceGovernor()
        constraints = gov.create_sandbox(
            name="my-vm",
            cpu_cores=8,
            memory_mb=65536,
            iops_limit=12800,
            throughput_mbps=290,
        )
        # ... run workload with gov.cgroup_path(name) ...
        gov.destroy_sandbox("my-vm")
    """

    def __init__(self) -> None:
        self._use_cgroup = _cgroup_v2_available()
        self._sandboxes: dict[str, AppliedConstraints] = {}
        if self._use_cgroup:
            logger.info("cgroup v2 available — using kernel enforcement")
        else:
            logger.info("cgroup v2 not available — using process-level enforcement")

    @property
    def enforcement_method(self) -> str:
        return "cgroupv2" if self._use_cgroup else "process"

    def cgroup_path(self, name: str) -> Optional[Path]:
        if not self._use_cgroup:
            return None
        return _CGROUP_ROOT / f"{_TWIN_PREFIX}-{name}"

    def create_sandbox(
        self,
        name: str,
        cpu_cores: int,
        memory_mb: int,
        iops_limit: int = 0,
        throughput_mbps: int = 0,
        net_bandwidth_mbps: int = 0,
    ) -> AppliedConstraints:
        """Create a resource-constrained sandbox for a digital-twin VM."""
        constraints = AppliedConstraints(
            cpu_cores=cpu_cores,
            memory_limit_bytes=memory_mb * 1024 * 1024,
            io_max_iops=iops_limit if iops_limit else None,
            io_max_bps=throughput_mbps * 1024 * 1024 if throughput_mbps else None,
            net_rate_mbit=net_bandwidth_mbps if net_bandwidth_mbps else None,
        )

        if self._use_cgroup:
            constraints = self._create_cgroup_sandbox(name, constraints)
        else:
            constraints = self._create_process_sandbox(name, constraints)

        self._sandboxes[name] = constraints
        return constraints

    def _create_cgroup_sandbox(
        self, name: str, constraints: AppliedConstraints
    ) -> AppliedConstraints:
        """Create a cgroup v2 sub-group with resource limits."""
        cg = _CGROUP_ROOT / f"{_TWIN_PREFIX}-{name}"
        cg.mkdir(exist_ok=True)
        constraints.cgroup_path = str(cg)
        constraints.method = "cgroupv2"

        # Enable controllers in parent if needed
        try:
            parent_subtree = _CGROUP_ROOT / "cgroup.subtree_control"
            needed = "+cpu +memory +io"
            parent_subtree.write_text(needed)
        except OSError:
            logger.debug("Could not enable all controllers in parent")

        # CPU: limit to N cores via cpu.max (quota/period)
        # quota = cores * period  =>  8 cores = 800000us / 100000us
        if constraints.cpu_cores is not None:
            quota_us = constraints.cpu_cores * constraints.cpu_period_us
            constraints.cpu_quota_us = quota_us
            try:
                (cg / "cpu.max").write_text(
                    f"{quota_us} {constraints.cpu_period_us}"
                )
                logger.info("CPU limit: %d cores (%d/%d us)",
                            constraints.cpu_cores, quota_us,
                            constraints.cpu_period_us)
            except OSError as e:
                logger.warning("Failed to set cpu.max: %s", e)

        # Memory: hard limit via memory.max
        if constraints.memory_limit_bytes is not None:
            try:
                (cg / "memory.max").write_text(str(constraints.memory_limit_bytes))
                # Disable swap to match Azure VM behavior
                try:
                    (cg / "memory.swap.max").write_text("0")
                except OSError:
                    pass
                logger.info("Memory limit: %d MB",
                            constraints.memory_limit_bytes // (1024 * 1024))
            except OSError as e:
                logger.warning("Failed to set memory.max: %s", e)

        # I/O: throttle via io.max on all block devices
        if constraints.io_max_iops or constraints.io_max_bps:
            self._apply_io_limits(cg, constraints)

        return constraints

    def _apply_io_limits(
        self, cg: Path, constraints: AppliedConstraints
    ) -> None:
        """Apply blkio throttling to all visible block devices."""
        try:
            # Find block device major:minor numbers
            dev_entries = []
            block_dir = Path("/sys/block")
            if block_dir.exists():
                for dev in block_dir.iterdir():
                    dev_file = Path(f"/dev/{dev.name}")
                    if dev_file.exists():
                        stat = os.stat(dev_file)
                        major = os.major(stat.st_rdev)
                        minor = os.minor(stat.st_rdev)
                        dev_entries.append(f"{major}:{minor}")

            if not dev_entries:
                # Fallback: try common device numbers
                dev_entries = ["8:0", "253:0"]

            for dev_id in dev_entries:
                parts = []
                if constraints.io_max_iops:
                    parts.append(f"riops={constraints.io_max_iops}")
                    parts.append(f"wiops={constraints.io_max_iops}")
                if constraints.io_max_bps:
                    parts.append(f"rbps={constraints.io_max_bps}")
                    parts.append(f"wbps={constraints.io_max_bps}")
                if parts:
                    line = f"{dev_id} {' '.join(parts)}\n"
                    try:
                        (cg / "io.max").write_text(line)
                    except OSError:
                        pass
            logger.info("I/O limits applied (iops=%s, bps=%s)",
                        constraints.io_max_iops, constraints.io_max_bps)
        except OSError as e:
            logger.warning("Failed to apply I/O limits: %s", e)

    def _create_process_sandbox(
        self, name: str, constraints: AppliedConstraints
    ) -> AppliedConstraints:
        """Fallback: record limits for process-level enforcement."""
        constraints.method = "process"

        if constraints.cpu_cores is not None:
            quota_us = constraints.cpu_cores * constraints.cpu_period_us
            constraints.cpu_quota_us = quota_us

        return constraints

    def apply_to_pid(self, name: str, pid: int) -> None:
        """Move a process into the sandbox's cgroup (or apply process limits)."""
        constraints = self._sandboxes.get(name)
        if constraints is None:
            raise ValueError(f"No sandbox named '{name}'")

        if constraints.method == "cgroupv2" and constraints.cgroup_path:
            try:
                procs_file = Path(constraints.cgroup_path) / "cgroup.procs"
                procs_file.write_text(str(pid))
                logger.info("PID %d moved to cgroup %s", pid, constraints.cgroup_path)
            except OSError as e:
                logger.warning("Failed to move PID %d to cgroup: %s", pid, e)
                self._apply_process_limits(constraints, pid)
        else:
            self._apply_process_limits(constraints, pid)

    def _apply_process_limits(
        self, constraints: AppliedConstraints, pid: int
    ) -> None:
        """Apply process-level limits via sched_setaffinity and setrlimit."""
        import resource

        if constraints.cpu_cores is not None:
            try:
                available = os.sched_getaffinity(0)
                target_cpus = set(list(available)[:constraints.cpu_cores])
                os.sched_setaffinity(pid, target_cpus)
                logger.info("CPU affinity for PID %d set to %s", pid, target_cpus)
            except OSError as e:
                logger.warning("Failed to set CPU affinity: %s", e)

        if constraints.memory_limit_bytes is not None:
            try:
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (constraints.memory_limit_bytes, constraints.memory_limit_bytes),
                )
                logger.info("Memory RLIMIT_AS for PID %d set to %d bytes",
                            pid, constraints.memory_limit_bytes)
            except (OSError, ValueError) as e:
                logger.warning("Failed to set memory limit: %s", e)

    def read_cpu_stats(self, name: str) -> dict:
        """Read CPU throttling stats from the cgroup."""
        constraints = self._sandboxes.get(name)
        stats = {"throttled_periods": 0, "throttled_time_us": 0}
        if not constraints or constraints.method != "cgroupv2":
            return stats
        try:
            stat_file = Path(constraints.cgroup_path) / "cpu.stat"
            if stat_file.exists():
                for line in stat_file.read_text().splitlines():
                    parts = line.split()
                    if len(parts) == 2:
                        if parts[0] == "nr_throttled":
                            stats["throttled_periods"] = int(parts[1])
                        elif parts[0] == "throttled_usec":
                            stats["throttled_time_us"] = int(parts[1])
        except OSError:
            pass
        return stats

    def read_memory_stats(self, name: str) -> dict:
        """Read memory usage and OOM events from the cgroup."""
        constraints = self._sandboxes.get(name)
        stats = {"current_bytes": 0, "oom_kill": 0}
        if not constraints or constraints.method != "cgroupv2":
            return stats
        cg = Path(constraints.cgroup_path)
        try:
            current = cg / "memory.current"
            if current.exists():
                stats["current_bytes"] = int(current.read_text().strip())
        except (OSError, ValueError):
            pass
        try:
            events = cg / "memory.events"
            if events.exists():
                for line in events.read_text().splitlines():
                    parts = line.split()
                    if len(parts) == 2 and parts[0] == "oom_kill":
                        stats["oom_kill"] = int(parts[1])
        except (OSError, ValueError):
            pass
        return stats

    def read_io_stats(self, name: str) -> dict:
        """Read I/O stats from the cgroup."""
        constraints = self._sandboxes.get(name)
        stats = {"rbytes": 0, "wbytes": 0, "rios": 0, "wios": 0}
        if not constraints or constraints.method != "cgroupv2":
            return stats
        try:
            stat_file = Path(constraints.cgroup_path) / "io.stat"
            if stat_file.exists():
                for line in stat_file.read_text().splitlines():
                    parts = line.split()
                    for part in parts[1:]:
                        if "=" in part:
                            key, val = part.split("=", 1)
                            if key in stats:
                                stats[key] += int(val)
        except (OSError, ValueError):
            pass
        return stats

    def get_constraints(self, name: str) -> Optional[AppliedConstraints]:
        return self._sandboxes.get(name)

    def destroy_sandbox(self, name: str) -> None:
        """Remove the cgroup sandbox and release resources."""
        constraints = self._sandboxes.pop(name, None)
        if constraints and constraints.method == "cgroupv2" and constraints.cgroup_path:
            cg = Path(constraints.cgroup_path)
            try:
                if cg.exists():
                    # Move all processes back to parent before removing
                    try:
                        procs = (cg / "cgroup.procs").read_text().split()
                        parent_procs = _CGROUP_ROOT / "cgroup.procs"
                        for pid in procs:
                            try:
                                parent_procs.write_text(pid)
                            except OSError:
                                pass
                    except OSError:
                        pass
                    cg.rmdir()
                    logger.info("Destroyed cgroup sandbox %s", cg)
            except OSError as e:
                logger.warning("Failed to destroy cgroup %s: %s", cg, e)

    def destroy_all(self) -> None:
        for name in list(self._sandboxes):
            self.destroy_sandbox(name)
