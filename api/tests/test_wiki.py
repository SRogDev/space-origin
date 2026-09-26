"""The wiki validator must pass on the shipped wiki content."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "scripts" / "validate_wiki.py"


def test_validator_exits_zero():
    r = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"validator failed:\n{r.stdout}\n{r.stderr}"
