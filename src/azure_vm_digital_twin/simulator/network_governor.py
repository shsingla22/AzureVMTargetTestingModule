"""Network bandwidth shaping via Linux tc (traffic control).

Enforces the network bandwidth limit of an E-series VM SKU by
applying a Token Bucket Filter (tbf) qdisc on a network interface.
Falls back to a no-op when tc is unavailable.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def _tc_available() -> bool:
    return shutil.which("tc") is not None


class NetworkGovernor:
    """Apply / remove network bandwidth limits via tc."""

    def __init__(self, interface: str = "eth0") -> None:
        self._interface = interface
        self._has_tc = _tc_available()
        self._active: dict[str, int] = {}  # name -> rate_mbit

    @property
    def available(self) -> bool:
        return self._has_tc

    def apply_limit(self, name: str, rate_mbit: int) -> bool:
        """Apply bandwidth limit. Returns True if enforcement succeeded."""
        if not self._has_tc or rate_mbit <= 0:
            self._active[name] = rate_mbit
            return False

        # Remove existing qdisc if any
        self._remove_qdisc()

        try:
            burst = max(rate_mbit * 1000, 10000)  # bytes
            latency_ms = 50
            subprocess.run(
                [
                    "tc", "qdisc", "add", "dev", self._interface,
                    "root", "tbf",
                    "rate", f"{rate_mbit}mbit",
                    "burst", str(burst),
                    "latency", f"{latency_ms}ms",
                ],
                check=True,
                capture_output=True,
            )
            self._active[name] = rate_mbit
            logger.info("Network limit %d Mbit/s applied on %s",
                        rate_mbit, self._interface)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Failed to apply tc limit: %s", e)
            self._active[name] = rate_mbit
            return False

    def remove_limit(self, name: str) -> None:
        self._active.pop(name, None)
        if not self._active:
            self._remove_qdisc()

    def _remove_qdisc(self) -> None:
        if not self._has_tc:
            return
        try:
            subprocess.run(
                ["tc", "qdisc", "del", "dev", self._interface, "root"],
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    def remove_all(self) -> None:
        self._active.clear()
        self._remove_qdisc()
