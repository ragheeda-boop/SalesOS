"""Unit tests for salesos/scripts/wave11-soak-gate.py classifiers.

Loads the script via importlib (lives outside backend package path).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_GATE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "wave11-soak-gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("wave11_soak_gate", _GATE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # dataclasses require the module to be present in sys.modules during exec
    import sys

    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gate():
    return _load_gate()


class TestClassifyHealthDetailed:
    def test_healthy_200_is_pass(self, gate):
        status, _ = gate.classify_health_detailed(
            200, {"status": "healthy", "checks": {"database": {"status": "connected"}}}
        )
        assert status == "PASS"

    def test_degraded_200_is_warn(self, gate):
        """Regression: soak 2026-08-09 marked degraded detailed as PASS."""
        status, detail = gate.classify_health_detailed(
            200,
            {
                "status": "degraded",
                "checks": {"database": {"status": "error", "message": "unavailable"}},
            },
        )
        assert status == "WARN"
        assert "degraded" in detail

    def test_db_error_even_if_overall_healthy_is_warn(self, gate):
        status, detail = gate.classify_health_detailed(
            200,
            {"status": "healthy", "checks": {"database": {"status": "error"}}},
        )
        assert status == "WARN"
        assert "database" in detail

    def test_http_400_is_warn(self, gate):
        status, _ = gate.classify_health_detailed(400, {})
        assert status == "WARN"

    def test_none_payload_200_is_pass(self, gate):
        status, _ = gate.classify_health_detailed(200, None)
        assert status == "PASS"
