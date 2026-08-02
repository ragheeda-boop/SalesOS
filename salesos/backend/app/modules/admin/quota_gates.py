"""STORY-06-03 — Path → quota metric gates (pure).

Seat/token/connector/storage dimensions tied to UsageMeter keys.
Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass

# Longest-prefix match. Metrics checked against Plan.entitlements.quotas (+ DOM-021).
# storage_mb piggybacks commercial surfaces (no dedicated upload gateway yet).
QUOTA_PATH_GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("/api/v1/rag", ("ai_tokens", "storage_mb")),
    ("/api/v1/ai", ("ai_tokens", "storage_mb")),
    ("/api/v1/copilot", ("ai_tokens", "storage_mb")),
    ("/api/v1/integrations", ("connectors", "storage_mb")),
    ("/api/v1/signals", ("storage_mb",)),
    # Seat burn — identity is domain-skipped; quota still applies on invite.
    ("/api/v1/identity/invite", ("seats",)),
)

# Mutating-only metrics: listing must remain readable when over connector quota.
MUTATING_ONLY_METRICS: frozenset[str] = frozenset({"connectors", "seats"})

MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True)
class QuotaGateMatch:
    path_prefix: str
    metrics: tuple[str, ...]


def quota_metrics_for_path(path: str, method: str = "GET") -> tuple[str, ...] | None:
    """Return metrics to enforce for path/method, or None if ungated."""
    path = path.split("?", 1)[0]
    best: QuotaGateMatch | None = None
    for prefix, metrics in QUOTA_PATH_GATES:
        matched = path == prefix or path.startswith(prefix + "/")
        if matched and (best is None or len(prefix) > len(best.path_prefix)):
            best = QuotaGateMatch(path_prefix=prefix, metrics=metrics)
    if best is None:
        return None
    method_u = (method or "GET").upper()
    if method_u in MUTATING_METHODS:
        return best.metrics
    # Safe methods: skip capacity gauges that only matter on create/mutate.
    filtered = tuple(m for m in best.metrics if m not in MUTATING_ONLY_METRICS)
    return filtered or None
