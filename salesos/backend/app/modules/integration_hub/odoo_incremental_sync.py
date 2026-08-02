"""STORY-09-07 — feature_odoo_integration Grade-A gate + incremental cursor pull.

``feature_odoo_integration`` is the ARB-mandated rollout flag (global off;
Muhide enabled via tenant override). write_date cursors persist per connection
model key. No invented Odoo secrets. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any

from app.modules.integration_hub.odoo_adapter import OdooAdapter
from app.modules.integration_hub.types import IncrementalCursor, PullRecord

# Exact program/ARB key (Grade-A admin_feature_flags).
FLAG_ODOO_INTEGRATION = "feature_odoo_integration"

# Design-partner slug — real tenant UUID resolved at ops time (no invented id).
MUHIDE_TENANT_SLUG = "muhide"


class OdooIntegrationDisabledError(PermissionError):
    """Raised when feature_odoo_integration evaluates disabled for the tenant."""


def evaluate_feature_odoo_integration(
    *,
    flag_found: bool,
    enabled: bool = False,
    tenant_overrides: Mapping[str, bool] | None = None,
    tenant_id: str,
    is_ci_test: bool = False,
    rollout_percentage: int = 100,
    tenant_ids_all: list[str] | None = None,
) -> dict[str, Any]:
    """Mirror PostgresFeatureFlagRepository.evaluate for unit / in-memory paths."""
    if not flag_found:
        return {"enabled": False, "reason": "flag_not_found"}
    if is_ci_test:
        return {"enabled": True, "reason": "ci_test_always_on"}
    overrides = dict(tenant_overrides or {})
    tid = str(tenant_id)
    if tid in overrides:
        return {"enabled": bool(overrides[tid]), "reason": "tenant_override"}
    if not enabled:
        return {"enabled": False, "reason": "globally_disabled"}
    if rollout_percentage >= 100:
        return {"enabled": True, "reason": "fully_rollout"}
    if rollout_percentage <= 0:
        return {"enabled": False, "reason": "zero_rollout"}
    if tenant_ids_all:
        sorted_ids = sorted(tenant_ids_all)
        try:
            idx = sorted_ids.index(tid)
        except ValueError:
            return {"enabled": False, "reason": "tenant_not_in_rollout_set"}
        ratio = idx / len(sorted_ids)
        included = ratio < (rollout_percentage / 100)
        return {
            "enabled": included,
            "reason": f"gradual_rollout_{rollout_percentage}pct",
        }
    return {"enabled": bool(enabled), "reason": "global_default"}


def assert_odoo_integration_enabled(flag_eval: Mapping[str, Any]) -> None:
    if flag_eval.get("enabled"):
        return
    reason = flag_eval.get("reason") or "disabled"
    raise OdooIntegrationDisabledError(f"{FLAG_ODOO_INTEGRATION} disabled ({reason})")


@dataclass
class MemConnectionCursorStore:
    """In-memory per-connection cursor_state (tests / CAP-028 without ORM)."""

    by_connection: dict[str, dict[str, str]] = field(default_factory=dict)

    def get_watermark(self, connection_id: str, model: str) -> str | None:
        state = self.by_connection.get(str(connection_id)) or {}
        raw = state.get((model or "").strip())
        return str(raw) if raw else None

    def set_watermark(self, connection_id: str, model: str, watermark: str) -> None:
        model_key = (model or "").strip()
        if not model_key:
            raise ValueError("model required")
        bucket = self.by_connection.setdefault(str(connection_id), {})
        bucket[model_key] = str(watermark)

    def as_cursor_state(self, connection_id: str) -> dict[str, str]:
        return dict(self.by_connection.get(str(connection_id)) or {})


def cursor_from_state(
    cursor_state: Mapping[str, Any] | None, model: str
) -> IncrementalCursor | None:
    model_key = (model or "").strip()
    if not model_key or not cursor_state:
        return None
    raw = cursor_state.get(model_key)
    if raw is None or str(raw).strip() == "":
        return None
    return IncrementalCursor(watermark=str(raw))


def apply_cursor_watermark(
    cursor_state: MutableMapping[str, Any],
    *,
    model: str,
    watermark: str,
) -> dict[str, Any]:
    model_key = (model or "").strip()
    if not model_key:
        raise ValueError("model required")
    out = dict(cursor_state or {})
    out[model_key] = str(watermark)
    return out


async def pull_odoo_incremental_for_sync(
    *,
    adapter: OdooAdapter,
    credential_ref: str,
    config: Mapping[str, Any],
    model: str,
    connection_id: str,
    tenant_id: str,
    flag_eval: Mapping[str, Any],
    cursor_store: MemConnectionCursorStore,
    limit: int = 100,
) -> dict[str, Any]:
    """Pull with write_date cursor; persist next watermark; honor rollout flag."""
    _ = tenant_id
    assert_odoo_integration_enabled(flag_eval)
    model_key = (model or "").strip() or "res.partner"
    before_wm = cursor_store.get_watermark(connection_id, model_key)
    cursor = IncrementalCursor(watermark=before_wm) if before_wm else None
    result = await adapter.pull_incremental(
        credential_ref=credential_ref,
        config=config,
        model=model_key,
        cursor=cursor,
        limit=limit,
    )
    after_wm = before_wm
    if result.next_cursor and result.next_cursor.watermark:
        after_wm = str(result.next_cursor.watermark)
        cursor_store.set_watermark(connection_id, model_key, after_wm)
    records: list[dict[str, Any]] = []
    for rec in result.records:
        if isinstance(rec, PullRecord):
            records.append(
                {
                    "id": rec.external_id,
                    "external_id": rec.external_id,
                    "model": rec.model,
                    "payload": dict(rec.payload),
                }
            )
        else:
            records.append(dict(rec))  # type: ignore[arg-type]
    return {
        "records": records,
        "failed": [],
        "cursor_before": {"write_date": before_wm} if before_wm else {},
        "cursor": {"write_date": after_wm} if after_wm else {},
    }
