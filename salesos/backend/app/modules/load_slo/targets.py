"""STORY-14-01 — Load / SLO targets (50-tenant pooled tier).

CI/non-prod harness companion for DevOps. Not Production GO.
No live prod kill. DEC-085 untouched. No FORCE RLS.
"""

from __future__ import annotations

TARGET_TENANTS = 50

# Synthetic CI SLO gates (companion shape for DevOps field harness).
P95_LATENCY_MS_MAX = 500.0
ERROR_RATE_MAX = 0.01

LOAD_PROFILES = frozenset(
    {
        "pooled_50_tenant_burst",
        "pooled_50_tenant_sustained_sim",
    }
)
