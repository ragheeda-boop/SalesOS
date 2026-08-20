"""Capability registry validation — pytest wrapper.

Runs the SoT-oriented validation gate (DEC-134 / Phase 0 criterion 5.3)
as a pytest test so it gates CI automatically.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_capability_registries.py"


@pytest.mark.skipif(not SCRIPT.exists(), reason="validation script not found")
class TestCapabilityRegistryValidation:
    def test_join_map_integrity(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--join-map-only"],
            capture_output=True,
            text=True,
            cwd=str(SCRIPT.parent.parent),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Join map integrity failed (exit {result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_sot_gate(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(SCRIPT.parent.parent),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"SoT gate failed (exit {result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
