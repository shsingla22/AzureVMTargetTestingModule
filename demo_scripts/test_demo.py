"""Test suite execution demo."""
import subprocess
import sys

result = subprocess.run(
    ["/usr/local/bin/python", "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=False,
)
sys.exit(result.returncode)
