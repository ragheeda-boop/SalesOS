"""STORY-06-02 — Path → DOM entitlement gate registry (pure).

At least 3 commercial DOM combinations mapped to live API prefixes.
Feature flags remain a separate layer. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass

# Longest-prefix match. Owner/admin/auth excluded via skip list in middleware.
ENTITLEMENT_PATH_GATES: tuple[tuple[str, str], ...] = (
    # DOM-011 AI/RAG
    ("/api/v1/rag", "DOM-011"),
    ("/api/v1/ai", "DOM-011"),
    # DOM-012 AI Studio (copilot surface)
    ("/api/v1/copilot", "DOM-012"),
    # DOM-023 GTM Intelligence
    ("/api/v1/signals", "DOM-023"),
    # DOM-021 Integration Hub
    ("/api/v1/integrations", "DOM-021"),
)

# Same skip family as suspend guard — Owner plane is not tenant-plan gated.
ENTITLEMENT_SKIP_PREFIXES: tuple[str, ...] = (
    "/health",
    "/ready",
    "/live",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/admin",
    "/api/v1/auth",
    "/api/v1/owner",
    "/api/v1/identity",
    "/api/v1/billing/stripe/webhook",
    "/api/health",
)


@dataclass(frozen=True)
class EntitlementGateMatch:
    path_prefix: str
    domain: str


def path_skips_entitlement_guard(path: str) -> bool:
    path = path.split("?", 1)[0]
    return any(path == p or path.startswith(p + "/") for p in ENTITLEMENT_SKIP_PREFIXES)


def required_domain_for_path(path: str) -> EntitlementGateMatch | None:
    """Return the most specific (longest) gate matching path, or None."""
    path = path.split("?", 1)[0]
    best: EntitlementGateMatch | None = None
    for prefix, domain in ENTITLEMENT_PATH_GATES:
        matched = path == prefix or path.startswith(prefix + "/")
        if matched and (best is None or len(prefix) > len(best.path_prefix)):
            best = EntitlementGateMatch(path_prefix=prefix, domain=domain)
    return best
