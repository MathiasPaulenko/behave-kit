"""Pytest test that runs behave on tests/e2e/features/ and asserts all pass."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FEATURES_DIR = Path(__file__).parent / "features"


def test_e2e_behave_features_pass() -> None:
    """Run behave on the E2E features directory (excluding timeout) and assert exit code 0."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "behave",
            str(FEATURES_DIR),
            "--no-capture",
            "--no-color",
            "--exclude",
            "timeout",
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


def test_e2e_timeout_feature() -> None:
    """Run the timeout features and verify expected pass/fail per scenario."""
    timeout_features = [
        FEATURES_DIR / "timeout.feature",
        FEATURES_DIR / "timeout_feature_inherit.feature",
    ]

    passing_scenarios = [
        "Scenario within default timeout passes",
        "Scenario with tag override that passes",
        "Tag timeout zero disables timeout",
        "Scenario inherits feature timeout and passes",
    ]

    failing_scenarios = [
        "Scenario exceeds tag timeout and fails",
        "Scenario exceeds default timeout and fails",
        "Scenario overrides feature timeout and fails",
    ]

    full_output = ""
    for feature_file in timeout_features:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "behave",
                str(feature_file),
                "--no-capture",
                "--no-color",
                "--format",
                "plain",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        full_output += result.stdout + "\n"

    for name in passing_scenarios:
        assert name in full_output, f"Missing scenario '{name}' in output:\n{full_output}"

    for name in failing_scenarios:
        assert name in full_output, f"Missing scenario '{name}' in output:\n{full_output}"

    # Verify passing scenarios actually passed (no failure or hook-error markers)
    for name in passing_scenarios:
        scenario_block = _extract_scenario_block(full_output, name)
        assert scenario_block is not None, f"Could not extract block for '{name}'"
        assert "failed" not in scenario_block.lower() and "HOOK-ERROR" not in scenario_block, (
            f"Scenario '{name}' should have passed but shows failure:\n{scenario_block}"
        )

    # Verify failing scenarios actually failed
    # On Unix: signal interrupts the step → "failed" in output
    # On Windows: ThreadTimer detects in after_scenario → "HOOK-ERROR" in output
    for name in failing_scenarios:
        scenario_block = _extract_scenario_block(full_output, name)
        assert scenario_block is not None, f"Could not extract block for '{name}'"
        assert "failed" in scenario_block.lower() or "HOOK-ERROR" in scenario_block, (
            f"Scenario '{name}' should have failed but shows no failure:\n{scenario_block}"
        )


def _extract_scenario_block(output: str, scenario_name: str) -> str | None:
    """Extract the text block for a single scenario from plain-format output."""
    lines = output.splitlines()
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if scenario_name in line:
            start_idx = i
            break
    if start_idx is None:
        return None

    block_lines = [lines[start_idx]]
    for line in lines[start_idx + 1 :]:
        # Stop at next scenario, feature, or summary section
        stripped = line.strip()
        if (
            line.startswith("  Scenario:")
            or line.startswith("Feature:")
            or stripped.startswith("Errored scenarios:")
            or stripped.startswith("Failing scenarios:")
            or stripped.startswith("0 features")
            or stripped.startswith("1 features")
            or stripped.startswith("2 features")
            or stripped
            and stripped[0].isdigit()
            and "features passed" in stripped
        ):
            break
        block_lines.append(line)
    return "\n".join(block_lines)
