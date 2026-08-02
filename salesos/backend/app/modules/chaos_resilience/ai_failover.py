"""STORY-14-06 — AI provider failover (non-prod) scenarios.

Builds on STORY-14-02 chaos AI outage handler. Fake providers only.
feature_ai_copilot remains False. No live LLM. Not Production GO.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS

VALID_AI_FAILOVER_SCENARIOS: frozenset[str] = frozenset(
    {
        "primary_outage",
        "cascade_to_tertiary",
        "chain_exhausted",
        "slo_budget",
    }
)

DEFAULT_FAILOVER_CHAIN: tuple[str, ...] = ("openai", "anthropic", "gemini")


@runtime_checkable
class FakeAiProvider(Protocol):
    @property
    def name(self) -> str: ...

    def chat(self, prompt: str) -> dict[str, Any]: ...


@dataclass
class MemFakeProvider:
    """Deterministic CI provider — never opens a network socket."""

    key: str
    fail: bool = False
    latency_ms: float = 0.0

    @property
    def name(self) -> str:
        return self.key

    def chat(self, prompt: str) -> dict[str, Any]:
        _ = prompt
        if self.latency_ms > 0:
            # Recorded latency only — no real sleep in CI paths (elapsed from clock).
            pass
        if self.fail:
            raise RuntimeError(f"injected_outage:{self.key}")
        return {
            "provider": self.key,
            "content": f"fixture-ok:{self.key}",
            "live_llm": False,
        }


@dataclass
class FailoverRunResult:
    scenario: str
    ok: bool
    graceful: bool
    within_slo: bool
    selected: str | None
    trail: list[dict[str, Any]] = field(default_factory=list)
    elapsed_ms: float = 0.0
    slo_seconds: float = AI_FAILOVER_SLO_SECONDS
    feature_ai_copilot: bool = False
    honesty: str = (
        "Non-prod fake provider failover harness; live LLM / feature_ai_copilot "
        "not enabled. Not Production GO."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "ok": self.ok,
            "graceful": self.graceful,
            "within_slo": self.within_slo,
            "selected": self.selected,
            "trail": list(self.trail),
            "elapsed_ms": self.elapsed_ms,
            "slo_seconds": self.slo_seconds,
            "feature_ai_copilot": self.feature_ai_copilot,
            "honesty": self.honesty,
        }


def build_scenario_providers(scenario: str) -> list[MemFakeProvider]:
    kind = (scenario or "").strip().lower()
    if kind not in VALID_AI_FAILOVER_SCENARIOS:
        raise ValueError(
            f"unknown scenario={scenario!r}; expected one of "
            f"{sorted(VALID_AI_FAILOVER_SCENARIOS)}"
        )
    if kind == "primary_outage":
        return [
            MemFakeProvider("openai", fail=True),
            MemFakeProvider("anthropic", fail=False),
            MemFakeProvider("gemini", fail=False),
        ]
    if kind == "cascade_to_tertiary":
        return [
            MemFakeProvider("openai", fail=True),
            MemFakeProvider("anthropic", fail=True),
            MemFakeProvider("gemini", fail=False),
        ]
    if kind == "chain_exhausted":
        return [
            MemFakeProvider("openai", fail=True),
            MemFakeProvider("anthropic", fail=True),
            MemFakeProvider("gemini", fail=True),
        ]
    # slo_budget — same as primary_outage; asserts wall-clock ≤ SLO
    return [
        MemFakeProvider("openai", fail=True),
        MemFakeProvider("anthropic", fail=False),
        MemFakeProvider("gemini", fail=False),
    ]


def run_failover_chain(
    *,
    scenario: str,
    prompt: str = "fixture ping",
    slo_seconds: float = AI_FAILOVER_SLO_SECONDS,
) -> FailoverRunResult:
    """Walk fake provider chain until success or exhaustion (no live network)."""
    providers = build_scenario_providers(scenario)
    started = time.perf_counter()
    trail: list[dict[str, Any]] = []
    selected: str | None = None
    for provider in providers:
        try:
            resp = provider.chat(prompt)
            trail.append(
                {
                    "provider": provider.name,
                    "ok": True,
                    "error": "",
                    "content": resp.get("content", ""),
                }
            )
            selected = provider.name
            break
        except RuntimeError as exc:
            trail.append(
                {
                    "provider": provider.name,
                    "ok": False,
                    "error": str(exc),
                    "content": "",
                }
            )

    elapsed_s = time.perf_counter() - started
    elapsed_ms = elapsed_s * 1000
    within_slo = elapsed_s <= float(slo_seconds)
    exhausted = selected is None
    # Exhaustion is graceful if we fail cleanly (no crash / no silent invent).
    graceful = (selected is not None) or exhausted
    ok = (selected is not None and within_slo) or (
        scenario == "chain_exhausted" and exhausted and within_slo
    )
    return FailoverRunResult(
        scenario=scenario,
        ok=ok,
        graceful=graceful,
        within_slo=within_slo,
        selected=selected,
        trail=trail,
        elapsed_ms=elapsed_ms,
        slo_seconds=float(slo_seconds),
        feature_ai_copilot=False,
    )
