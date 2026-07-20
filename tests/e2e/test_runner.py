"""Pytest test that runs behave on tests/e2e/features/ and asserts all pass."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FEATURES_DIR = Path(__file__).parent / "features"


def test_e2e_behave_features_pass() -> None:
    """Run behave on the E2E features directory and assert exit code 0."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "behave",
            str(FEATURES_DIR),
            "--no-capture",
            "--no-color",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Behave E2E tests failed (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
