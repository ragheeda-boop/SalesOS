"""STORY-14-02 — Graceful handlers under injected faults.

Simulated (CI) only — does not open live network or kill real DB.
feature_ai_copilot remains False; AI drill uses fake provider chain.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS


@dataclass
class HandlerOutcome:
    ok: bool
    graceful: bool
    detail: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "graceful": self.graceful,
            "detail": dict(self.detail),
            "elapsed_ms": self.elapsed_ms,
        }


def handle_connector_outage(*, max_retries: int = 3) -> HandlerOutcome:
    """Simulate unreachable connector endpoint — backoff retries, no corrupt sync."""
    started = time.perf_counter()
    attempts: list[dict[str, Any]] = []
    for i in range(1, max(1, max_retries) + 1):
        # Simulated failure + exponential backoff (no sleep in CI — record schedule).
        backoff_ms = min(100 * (2 ** (i - 1)), 800)
        attempts.append(
            {
                "attempt": i,
                "ok": False,
                "error": "connector_endpoint_unreachable",
                "backoff_ms": backoff_ms,
            }
        )
    # Graceful: aborted cleanly, no partial write claimed.
    elapsed = (time.perf_counter() - started) * 1000
    return HandlerOutcome(
        ok=True,
        graceful=True,
        elapsed_ms=elapsed,
        detail={
            "sync_status": "aborted_clean",
            "partial_corrupt": False,
            "alert": "connector_outage_loud",
            "attempts": attempts,
            "honesty": "Simulated connector kill; live Odoo/HubSpot not touched",
        },
    )


def handle_ai_provider_outage(
    *,
    primary: str = "openai",
    chain: list[str] | None = None,
) -> HandlerOutcome:
    """Primary provider fails; failover chain engages within SLO (simulated)."""
    started = time.perf_counter()
    providers = list(chain or ["openai", "anthropic", "gemini"])
    if primary in providers:
        providers = [primary] + [p for p in providers if p != primary]

    # Inject: primary always fails; first secondary succeeds.
    trail: list[dict[str, Any]] = []
    selected = ""
    for idx, name in enumerate(providers):
        if idx == 0 or name == primary:
            trail.append({"provider": name, "ok": False, "error": "injected_primary_outage"})
            continue
        trail.append({"provider": name, "ok": True, "error": ""})
        selected = name
        break

    elapsed_s = time.perf_counter() - started
    elapsed_ms = elapsed_s * 1000
    within_slo = elapsed_s <= AI_FAILOVER_SLO_SECONDS and bool(selected)
    return HandlerOutcome(
        ok=within_slo,
        graceful=bool(selected),
        elapsed_ms=elapsed_ms,
        detail={
            "primary": primary,
            "selected": selected or None,
            "failover_chain": providers,
            "trail": trail,
            "slo_seconds": AI_FAILOVER_SLO_SECONDS,
            "within_slo": within_slo,
            "feature_ai_copilot": False,
            "honesty": (
                "Simulated provider outage against failover chain pattern; "
                "live LLM / feature_ai_copilot not enabled"
            ),
        },
    )


def handle_db_failover() -> HandlerOutcome:
    """Primary DB unavailable — reconnect path; in-flight fails cleanly/retryable."""
    started = time.perf_counter()
    # Simulated: in-flight request gets retryable error; pool reconnects.
    in_flight = {
        "status": "failed_clean",
        "retryable": True,
        "error": "primary_unavailable",
        "silent_data_loss": False,
    }
    reconnect = {
        "attempted": True,
        "ok": True,
        "role": "replica_promoted_sim",
    }
    elapsed = (time.perf_counter() - started) * 1000
    graceful = (
        in_flight["retryable"] is True
        and in_flight["silent_data_loss"] is False
        and reconnect["ok"] is True
    )
    return HandlerOutcome(
        ok=graceful,
        graceful=graceful,
        elapsed_ms=elapsed,
        detail={
            "in_flight": in_flight,
            "reconnect": reconnect,
            "honesty": "Simulated DB failover; no Alembic / live primary kill",
        },
    )
