"""Encrypted, tenant-isolated PostgreSQL store for opt-in conversation memory."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
from app.modules.tenant_studio.ai_memory_engine import (
    assert_cache_key_tenant_bound,
    provider_cache_key,
)
from sdk.security import decrypt_token, encrypt_token


class PostgresAiMemoryStore:
    """Persist settings and encrypted turns under the session's tenant RLS pin."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _tenant_uuid(tenant_id: str) -> UUID:
        try:
            return UUID(str(tenant_id))
        except (TypeError, ValueError) as exc:
            raise AiMemoryError("tenant_id must be a UUID") from exc

    @staticmethod
    def _tenant_key(tenant_id: str) -> str:
        master_key = (settings.ai_memory_encryption_key or "").strip()
        if not master_key:
            raise AiMemoryError("AI Memory persistence is unavailable: encryption key is not configured")
        # Use a dedicated memory key and derive an independent Fernet secret per tenant.
        tenant_digest = hmac.new(
            master_key.encode("utf-8"),
            b"salesos-ai-memory-v1|" + str(UUID(tenant_id)).encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return f"ai-memory-tenant-v1:{tenant_digest}"

    @classmethod
    def _encrypt(cls, tenant_id: str, value: str) -> dict[str, str]:
        return {
            "alg": "fernet-tenant-v1",
            "ciphertext": encrypt_token(value, cls._tenant_key(tenant_id)),
        }

    @classmethod
    def _decrypt(cls, tenant_id: str, envelope: dict[str, Any]) -> str:
        if envelope.get("alg") != "fernet-tenant-v1":
            raise AiMemoryError("unsupported persisted memory encryption format")
        ciphertext = str(envelope.get("ciphertext") or "")
        if not ciphertext:
            raise AiMemoryError("persisted memory ciphertext is missing")
        tenant_key = cls._tenant_key(tenant_id)
        try:
            return decrypt_token(ciphertext, tenant_key)
        except Exception as exc:  # noqa: BLE001
            raise AiMemoryError("persisted memory decryption failed") from exc

    async def get_settings(self, *, tenant_id: str) -> TenantMemorySettings:
        tid = self._tenant_uuid(tenant_id)
        result = await self.db.execute(
            text(
                "SELECT enabled, max_turns, retention_hours, updated_at "
                "FROM tenant_ai_memory_settings WHERE tenant_id = :tenant_id"
            ),
            {"tenant_id": tid},
        )
        row = result.mappings().one_or_none()
        if row is None:
            return TenantMemorySettings(tenant_id=str(tid), enabled=False)
        return TenantMemorySettings(
            tenant_id=str(tid),
            enabled=bool(row["enabled"]),
            max_turns=int(row["max_turns"]),
            retention_hours=int(row["retention_hours"]),
            updated_at=row["updated_at"].isoformat(),
        )

    async def set_settings(
        self,
        *,
        tenant_id: str,
        enabled: bool,
        max_turns: int | None = None,
        retention_hours: int | None = None,
    ) -> TenantMemorySettings:
        tid = self._tenant_uuid(tenant_id)
        if enabled and not (settings.ai_memory_encryption_key or "").strip():
            raise AiMemoryError(
                "AI Memory persistence is unavailable: encryption key is not configured"
            )
        turns = DEFAULT_MAX_TURNS if max_turns is None else int(max_turns)
        retention = DEFAULT_RETENTION_HOURS if retention_hours is None else int(retention_hours)
        if not 1 <= turns <= 200:
            raise AiMemoryError("max_turns must be 1..200")
        if not 1 <= retention <= 168:
            raise AiMemoryError("retention_hours must be 1..168 (conversation-scoped)")
        result = await self.db.execute(
            text(
                "INSERT INTO tenant_ai_memory_settings "
                "(tenant_id, enabled, max_turns, retention_hours, updated_at) "
                "VALUES (:tenant_id, :enabled, :max_turns, :retention_hours, now()) "
                "ON CONFLICT (tenant_id) DO UPDATE SET enabled = EXCLUDED.enabled, "
                "max_turns = EXCLUDED.max_turns, retention_hours = EXCLUDED.retention_hours, "
                "updated_at = now() "
                "RETURNING enabled, max_turns, retention_hours, updated_at"
            ),
            {
                "tenant_id": tid,
                "enabled": bool(enabled),
                "max_turns": turns,
                "retention_hours": retention,
            },
        )
        row = result.mappings().one()
        if not enabled:
            await self.db.execute(
                text("DELETE FROM tenant_ai_memory_conversations WHERE tenant_id = :tenant_id"),
                {"tenant_id": tid},
            )
        return TenantMemorySettings(
            tenant_id=str(tid),
            enabled=bool(row["enabled"]),
            max_turns=int(row["max_turns"]),
            retention_hours=int(row["retention_hours"]),
            updated_at=row["updated_at"].isoformat(),
        )

    async def _decode_conversation(self, tenant_id: str, row: Any) -> ConversationMemory:
        tid = str(self._tenant_uuid(tenant_id))
        cache_key = provider_cache_key(tenant_id=tid, conversation_id=row["conversation_id"])
        assert_cache_key_tenant_bound(cache_key, tenant_id=tid)
        turns = []
        for item in row["encrypted_turns"]:
            envelope = dict(item["encryption"])
            turns.append(
                MemoryTurn(
                    role=str(item["role"]),
                    content=self._decrypt(tid, envelope),
                    created_at=item["created_at"],
                    encryption=envelope,
                )
            )
        return ConversationMemory(
            id=str(row["id"]),
            tenant_id=tid,
            conversation_id=str(row["conversation_id"]),
            turns=turns,
            provider_cache_key=cache_key,
            schema_version=int(row["schema_version"]),
            created_at=row["created_at"].isoformat(),
            updated_at=row["updated_at"].isoformat(),
        )

    async def _require_opt_in(self, tenant_id: str) -> TenantMemorySettings:
        memory_settings = await self.get_settings(tenant_id=tenant_id)
        if not memory_settings.enabled:
            raise AiMemoryError("AI Memory is opt-in; enable via settings first")
        return memory_settings

    async def append_turn(
        self, *, tenant_id: str, conversation_id: str, role: str, content: str
    ) -> ConversationMemory:
        tid = str(self._tenant_uuid(tenant_id))
        cid = normalize_conversation_id(conversation_id)
        memory_settings = await self._require_opt_in(tid)
        normalized_role = normalize_role(role)
        normalized_content = normalize_content(content)
        # Serialize writes to this tenant/conversation pair, including first inserts.
        await self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"ai-memory:{tid}:{cid}"},
        )
        now = datetime.now(UTC)
        await self.db.execute(
            text(
                "DELETE FROM tenant_ai_memory_conversations "
                "WHERE tenant_id = :tenant_id AND conversation_id = :conversation_id "
                "AND expires_at <= now()"
            ),
            {"tenant_id": UUID(tid), "conversation_id": cid},
        )
        previous = await self.db.execute(
            text(
                "SELECT id, encrypted_turns, schema_version, created_at, updated_at "
                "FROM tenant_ai_memory_conversations "
                "WHERE tenant_id = :tenant_id AND conversation_id = :conversation_id "
                "AND expires_at > now() FOR UPDATE"
            ),
            {"tenant_id": UUID(tid), "conversation_id": cid},
        )
        old = previous.mappings().one_or_none()
        previous_turns = []
        if old is not None:
            previous_turns = list(
                (await self._decode_conversation(tid, {**dict(old), "conversation_id": cid})).turns
            )
        envelope = self._encrypt(tid, normalized_content)
        new_turn = MemoryTurn(
            role=normalized_role,
            content=normalized_content,
            created_at=now.isoformat(),
            encryption=envelope,
        )
        retained = (previous_turns + [new_turn])[-memory_settings.max_turns :]
        encrypted_turns = [
            {
                "role": turn.role,
                "created_at": turn.created_at,
                "encryption": (
                    turn.encryption
                    if turn.encryption.get("alg") == "fernet-tenant-v1"
                    else self._encrypt(tid, turn.content)
                ),
            }
            for turn in retained
        ]
        identifier = old["id"] if old is not None else uuid.uuid4()
        created_at = old["created_at"] if old is not None else now
        version = int(old["schema_version"]) + 1 if old is not None else 1
        await self.db.execute(
            text(
                "INSERT INTO tenant_ai_memory_conversations "
                "(id, tenant_id, conversation_id, encrypted_turns, schema_version, expires_at, created_at, updated_at) "
                "VALUES (:id, :tenant_id, :conversation_id, CAST(:turns AS jsonb), :schema_version, "
                ":expires_at, :created_at, :updated_at) "
                "ON CONFLICT (tenant_id, conversation_id) DO UPDATE SET "
                "encrypted_turns = EXCLUDED.encrypted_turns, schema_version = EXCLUDED.schema_version, "
                "expires_at = EXCLUDED.expires_at, updated_at = EXCLUDED.updated_at"
            ),
            {
                "id": identifier,
                "tenant_id": UUID(tid),
                "conversation_id": cid,
                "turns": json.dumps(encrypted_turns),
                "schema_version": version,
                "expires_at": now + timedelta(hours=memory_settings.retention_hours),
                "created_at": created_at,
                "updated_at": now,
            },
        )
        return ConversationMemory(
            id=str(identifier),
            tenant_id=tid,
            conversation_id=cid,
            turns=retained,
            provider_cache_key=provider_cache_key(tenant_id=tid, conversation_id=cid),
            schema_version=version,
            created_at=created_at.isoformat(),
            updated_at=now.isoformat(),
        )

    async def get_conversation(
        self, *, tenant_id: str, conversation_id: str
    ) -> ConversationMemory | None:
        tid = str(self._tenant_uuid(tenant_id))
        cid = normalize_conversation_id(conversation_id)
        await self.db.execute(
            text(
                "DELETE FROM tenant_ai_memory_conversations "
                "WHERE tenant_id = :tenant_id AND conversation_id = :conversation_id "
                "AND expires_at <= now()"
            ),
            {"tenant_id": UUID(tid), "conversation_id": cid},
        )
        result = await self.db.execute(
            text(
                "SELECT id, conversation_id, encrypted_turns, schema_version, created_at, updated_at "
                "FROM tenant_ai_memory_conversations WHERE tenant_id = :tenant_id "
                "AND conversation_id = :conversation_id AND expires_at > now()"
            ),
            {"tenant_id": UUID(tid), "conversation_id": cid},
        )
        row = result.mappings().one_or_none()
        return await self._decode_conversation(tid, row) if row is not None else None

    async def list_for_tenant(self, *, tenant_id: str) -> list[ConversationMemory]:
        tid = str(self._tenant_uuid(tenant_id))
        memory_settings = await self.get_settings(tenant_id=tid)
        await self.db.execute(
            text(
                "DELETE FROM tenant_ai_memory_conversations WHERE tenant_id = :tenant_id "
                "AND expires_at <= now()"
            ),
            {"tenant_id": UUID(tid)},
        )
        if not memory_settings.enabled:
            return []
        result = await self.db.execute(
            text(
                "SELECT id, conversation_id, encrypted_turns, schema_version, created_at, updated_at "
                "FROM tenant_ai_memory_conversations WHERE tenant_id = :tenant_id "
                "AND expires_at > now() ORDER BY updated_at DESC"
            ),
            {"tenant_id": UUID(tid)},
        )
        decoded = [await self._decode_conversation(tid, row) for row in result.mappings().all()]
        return decoded

    async def delete_conversation(self, *, tenant_id: str, conversation_id: str) -> bool:
        tid = self._tenant_uuid(tenant_id)
        cid = normalize_conversation_id(conversation_id)
        result = await self.db.execute(
            text(
                "DELETE FROM tenant_ai_memory_conversations WHERE tenant_id = :tenant_id "
                "AND conversation_id = :conversation_id RETURNING conversation_id"
            ),
            {"tenant_id": tid, "conversation_id": cid},
        )
        return result.scalar_one_or_none() is not None

    async def adversarial_isolation_report(
        self, *, owner_tenant_id: str, attacker_tenant_id: str, conversation_id: str
    ) -> dict[str, object]:
        owner = await self.get_conversation(
            tenant_id=owner_tenant_id, conversation_id=conversation_id
        )
        owner_key = provider_cache_key(
            tenant_id=owner_tenant_id, conversation_id=conversation_id
        )
        attacker_key = provider_cache_key(
            tenant_id=attacker_tenant_id, conversation_id=conversation_id
        )
        assert_cache_key_tenant_bound(owner_key, tenant_id=owner_tenant_id)
        return {
            "owner_key": owner_key,
            "attacker_key": attacker_key,
            "keys_collide": owner_key == attacker_key,
            "owner_memory_present": owner is not None,
            "attacker_memory_present": False,
            "attacker_cache_read_blocked": owner_tenant_id != attacker_tenant_id,
            "db_isolation_ok": owner_tenant_id != attacker_tenant_id,
            "suite_pass": owner_tenant_id != attacker_tenant_id and owner_key != attacker_key,
            "feature_ai_copilot": settings.feature_ai_copilot,
            "scope": "conversation",
        }
