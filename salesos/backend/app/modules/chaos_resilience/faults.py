"""STORY-14-02 — Chaos / Phase 6 resilience fault kinds.

In-memory fault injection only. Not Production GO. No live ERP/DB kill.
"""

from __future__ import annotations

from typing import Literal

FaultKind = Literal[
    "connector_outage",
    "ai_provider_outage",
    "db_failover",
]

VALID_FAULT_KINDS: frozenset[str] = frozenset(
    {
        "connector_outage",
        "ai_provider_outage",
        "db_failover",
    }
)

# PRODUCTION_READINESS_CHECKLIST — AI failover SLO (seconds).
AI_FAILOVER_SLO_SECONDS = 30.0
