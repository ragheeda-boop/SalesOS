"""STORY-12-03 — AI Memory engine (provider-cache key isolation).

Honesty: fixture provider-cache shape only — no live LLM provider calls.
Tenant id is mandatory in cache keys to prevent shared-provider leakage.
"""

from __future__ import annotations

import hashlib

from app.modules.tenant_studio.ai_memory import AiMemoryError


def provider_cache_key(
    *,
    tenant_id: str,
    conversation_id: str,
    provider: str = "fixture",
) -> str:
    """Derive a provider-cache-shaped key that cannot collide across tenants.

    Adversarial requirement: shared model-provider prompt caches must not
    allow tenant B to retrieve tenant A's conversation context by conversation_id
    alone. tenant_id is therefore a mandatory key segment.
    """
    tid = (tenant_id or "").strip()
    cid = (conversation_id or "").strip()
    prov = (provider or "fixture").strip() or "fixture"
    if not tid:
        raise AiMemoryError("tenant_id required for provider cache key")
    if not cid:
        raise AiMemoryError("conversation_id required for provider cache key")
    raw = f"{prov}|{tid}|{cid}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"pcm:{prov}:t={tid}:c={cid}:h={digest}"


def assert_cache_key_tenant_bound(cache_key: str, *, tenant_id: str) -> None:
    """Reject cache keys that omit or mismatch the calling tenant."""
    tid = (tenant_id or "").strip()
    if not tid:
        raise AiMemoryError("tenant_id required")
    marker = f":t={tid}:"
    if marker not in (cache_key or ""):
        raise AiMemoryError("provider cache key tenant mismatch blocked")


def adversarial_probe_cross_tenant_cache(
    *,
    owner_tenant_id: str,
    attacker_tenant_id: str,
    conversation_id: str,
) -> dict[str, object]:
    """Simulate shared-provider cache probe: attacker must not resolve owner key."""
    owner_key = provider_cache_key(
        tenant_id=owner_tenant_id,
        conversation_id=conversation_id,
    )
    attacker_key = provider_cache_key(
        tenant_id=attacker_tenant_id,
        conversation_id=conversation_id,
    )
    leaked = owner_key == attacker_key
    blocked = True
    try:
        assert_cache_key_tenant_bound(owner_key, tenant_id=attacker_tenant_id)
        blocked = False
    except AiMemoryError:
        blocked = True
    return {
        "owner_key": owner_key,
        "attacker_key": attacker_key,
        "keys_collide": leaked,
        "attacker_bound_check_blocked": blocked,
        "isolation_ok": (not leaked) and blocked,
        "live_llm": False,
    }
