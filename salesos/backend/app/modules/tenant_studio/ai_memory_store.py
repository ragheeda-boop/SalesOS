"""STORY-12-03 — In-memory AI Memory store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.modules.tenant_studio.ai_memory import (
    DEFAULT_MAX_TURNS,
    DEFAULT_RETENTION_HOURS,
    AiMemoryError,
    ConversationMemory,
    MemoryTurn,
    TenantMemorySettings,
    normalize_content,
    normalize_conversation_id,
    normalize_role,
)
from app.modules.tenant_studio.ai_memory_crypto import decrypt_content, encrypt_content
from app.modules.tenant_studio.ai_memory_engine import (
    adversarial_probe_cross_tenant_cache,
    assert_cache_key_tenant_bound,
    provider_cache_key,
)


@dataclass
class MemAiMemoryStore:
    """Tenant-scoped conversation memory + opt-in settings + provider cache map."""

    _settings: dict[str, TenantMemorySettings] = field(default_factory=dict)
    _by_conv: dict[tuple[str, str], ConversationMemory] = field(default_factory=dict)
    # Simulated shared provider prompt-cache (adversarial isolation target).
    _provider_cache: dict[str, str] = field(default_factory=dict)

    def get_settings(self, *, tenant_id: str) -> TenantMemorySettings:
        tid = (tenant_id or "").strip()
        if not tid:
            raise AiMemoryError("tenant_id required")
        row = self._settings.get(tid)
        if row is None:
            row = TenantMemorySettings(tenant_id=tid, enabled=False)
            self._settings[tid] = row
        return row

    def set_settings(
        self,
        *,
        tenant_id: str,
        enabled: bool,
        max_turns: int | None = None,
        retention_hours: int | None = None,
    ) -> TenantMemorySettings:
        tid = (tenant_id or "").strip()
        if not tid:
            raise AiMemoryError("tenant_id required")
        mt = DEFAULT_MAX_TURNS if max_turns is None else int(max_turns)
        rh = DEFAULT_RETENTION_HOURS if retention_hours is None else int(retention_hours)
        if mt < 1 or mt > 200:
            raise AiMemoryError("max_turns must be 1..200")
        if rh < 1 or rh > 168:
            raise AiMemoryError("retention_hours must be 1..168 (conversation-scoped)")
        now = datetime.now(UTC).isoformat()
        row = TenantMemorySettings(
            tenant_id=tid,
            enabled=bool(enabled),
            max_turns=mt,
            retention_hours=rh,
            updated_at=now,
        )
        self._settings[tid] = row
        return row

    def _require_opt_in(self, tenant_id: str) -> TenantMemorySettings:
        settings = self.get_settings(tenant_id=tenant_id)
        if not settings.enabled:
            raise AiMemoryError("AI Memory is opt-in; enable via settings first")
        return settings

    def _is_expired(self, row: ConversationMemory, settings: TenantMemorySettings) -> bool:
        if not row.updated_at:
            return False
        try:
            updated = datetime.fromisoformat(row.updated_at)
        except ValueError:
            return False
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        age = datetime.now(UTC) - updated
        return age > timedelta(hours=int(settings.retention_hours))

    def _purge_if_expired(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
    ) -> None:
        tid = str(tenant_id)
        cid = normalize_conversation_id(conversation_id)
        key = (tid, cid)
        row = self._by_conv.get(key)
        if row is None:
            return
        settings = self.get_settings(tenant_id=tid)
        if self._is_expired(row, settings):
            self._by_conv.pop(key, None)
            self._provider_cache.pop(row.provider_cache_key, None)

    def append_turn(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        role: str,
        content: str,
    ) -> ConversationMemory:
        tid = (tenant_id or "").strip()
        if not tid:
            raise AiMemoryError("tenant_id required")
        settings = self._require_opt_in(tid)
        cid = normalize_conversation_id(conversation_id)
        self._purge_if_expired(tenant_id=tid, conversation_id=cid)
        r = normalize_role(role)
        body = normalize_content(content)
        now = datetime.now(UTC).isoformat()
        key = (tid, cid)
        existing = self._by_conv.get(key)
        cache_key = provider_cache_key(tenant_id=tid, conversation_id=cid)
        assert_cache_key_tenant_bound(cache_key, tenant_id=tid)

        envelope = encrypt_content(tenant_id=tid, plaintext=body)
        # Owner API surface returns plaintext; at-rest keeps envelope.
        turn = MemoryTurn(role=r, content=body, created_at=now, encryption=envelope)
        if existing is None:
            row = ConversationMemory(
                id=uuid.uuid4().hex[:12],
                tenant_id=tid,
                conversation_id=cid,
                turns=[turn],
                provider_cache_key=cache_key,
                schema_version=1,
                created_at=now,
                updated_at=now,
            )
        else:
            turns = list(existing.turns) + [turn]
            if len(turns) > settings.max_turns:
                turns = turns[-settings.max_turns :]
            row = ConversationMemory(
                id=existing.id,
                tenant_id=tid,
                conversation_id=cid,
                turns=turns,
                provider_cache_key=cache_key,
                schema_version=existing.schema_version + 1,
                created_at=existing.created_at,
                updated_at=now,
            )
        self._by_conv[key] = row
        # Provider cache stores only a tenant-bound opaque fingerprint — never
        # raw cross-tenant readable payload keyed by conversation_id alone.
        self._provider_cache[cache_key] = f"turns={len(row.turns)};tenant={tid}"
        return row

    def get_conversation(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
    ) -> ConversationMemory | None:
        tid = str(tenant_id)
        cid = normalize_conversation_id(conversation_id)
        self._purge_if_expired(tenant_id=tid, conversation_id=cid)
        row = self._by_conv.get((tid, cid))
        if row is None:
            return None
        # Fail closed if stored envelopes cannot decrypt under this tenant.
        for turn in row.turns:
            if turn.encryption:
                plain = decrypt_content(tenant_id=tid, envelope=turn.encryption)
                if plain != turn.content:
                    raise AiMemoryError("encryption integrity mismatch")
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[ConversationMemory]:
        tid = str(tenant_id)
        settings = self.get_settings(tenant_id=tid)
        expired_keys = [
            key
            for key, m in self._by_conv.items()
            if key[0] == tid and self._is_expired(m, settings)
        ]
        for key in expired_keys:
            row = self._by_conv.pop(key, None)
            if row is not None:
                self._provider_cache.pop(row.provider_cache_key, None)
        return sorted(
            [m for (t, _), m in self._by_conv.items() if t == tid],
            key=lambda m: m.updated_at or "",
            reverse=True,
        )

    def delete_conversation(self, *, tenant_id: str, conversation_id: str) -> bool:
        tid = str(tenant_id)
        cid = normalize_conversation_id(conversation_id)
        key = (tid, cid)
        row = self._by_conv.pop(key, None)
        if row is None:
            return False
        self._provider_cache.pop(row.provider_cache_key, None)
        return True

    def read_provider_cache(self, *, tenant_id: str, cache_key: str) -> str | None:
        """Tenant-bound provider-cache read (adversarial isolation gate)."""
        assert_cache_key_tenant_bound(cache_key, tenant_id=tenant_id)
        return self._provider_cache.get(cache_key)

    def adversarial_isolation_report(
        self,
        *,
        owner_tenant_id: str,
        attacker_tenant_id: str,
        conversation_id: str,
    ) -> dict[str, object]:
        probe = adversarial_probe_cross_tenant_cache(
            owner_tenant_id=owner_tenant_id,
            attacker_tenant_id=attacker_tenant_id,
            conversation_id=conversation_id,
        )
        owner = self.get_conversation(
            tenant_id=owner_tenant_id,
            conversation_id=conversation_id,
        )
        attacker_view = self.get_conversation(
            tenant_id=attacker_tenant_id,
            conversation_id=conversation_id,
        )
        owner_cache = None
        attacker_cache_blocked = False
        if owner is not None:
            owner_cache = self.read_provider_cache(
                tenant_id=owner_tenant_id,
                cache_key=owner.provider_cache_key,
            )
            try:
                self.read_provider_cache(
                    tenant_id=attacker_tenant_id,
                    cache_key=owner.provider_cache_key,
                )
            except AiMemoryError:
                attacker_cache_blocked = True
        return {
            **probe,
            "owner_memory_present": owner is not None,
            "attacker_memory_present": attacker_view is not None,
            "owner_cache_hit": owner_cache is not None,
            "attacker_cache_read_blocked": attacker_cache_blocked or owner is None,
            "db_isolation_ok": attacker_view is None,
            "suite_pass": bool(probe.get("isolation_ok"))
            and attacker_view is None
            and (attacker_cache_blocked or owner is None),
            "feature_ai_copilot": False,
            "scope": "conversation",
        }


DEFAULT_AI_MEMORY_STORE = MemAiMemoryStore()
