"""STORY-09-02 — crm.lead Opportunity pull → ACL with translated stages.

Odoo stage semantics are mapped to canonical SalesOS stages; raw stage
ids/names are never persisted. No invented secrets. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    CanonicalRecord,
    OdooTranslator,
)
from app.modules.integration_hub.types import PullRecord

# Canonical commercial pipeline stages (domains/commercial).
CANONICAL_OPPORTUNITY_STAGES = frozenset(
    {
        "prospecting",
        "qualification",
        "proposal",
        "negotiation",
        "closed_won",
        "closed_lost",
    }
)

# Example Odoo crm.stage → canonical map for certify/CI (not tenant secrets).
# Tenant-specific maps come from FieldMappingConfig / connection config.
DEFAULT_ODOO_OPPORTUNITY_STAGE_MAP: dict[str, str] = {
    "1": "prospecting",
    "2": "qualification",
    "3": "proposal",
    "4": "negotiation",
    "won": "closed_won",
    "lost": "closed_lost",
    # Common stage name aliases (when stage_id resolves to name string)
    "new": "prospecting",
    "qualified": "qualification",
    "proposition": "proposal",
}

# Required pull fields only — optional Odoo columns (description/currency) mapped
# after ACL when present so empty description does not block stage translation AC.
DEFAULT_OPPORTUNITY_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "name", "external": "name", "direction": "pull"},
    {"internal": "stage", "external": "stage_id", "direction": "pull"},
    {"internal": "amount", "external": "expected_revenue", "direction": "pull"},
    {"internal": "partner_external_id", "external": "partner_id", "direction": "pull"},
]

_OPTIONAL_OPPORTUNITY_EXTERNALS: tuple[tuple[str, str], ...] = (
    ("note", "description"),
    ("currency", "currency_id"),
)


@dataclass
class OpportunitySyncItem:
    external_id: str
    record: CanonicalRecord
    partner_external_id: str | None = None


@dataclass
class OpportunitySyncBatchResult:
    synced: list[OpportunitySyncItem] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.synced) + len(self.failed)


def opportunity_translator(
    stage_map: Mapping[str, str] | None = None,
) -> OdooTranslator:
    """ACL configured for Opportunity — strict stage translation (no passthrough)."""
    return OdooTranslator(
        stage_map=dict(stage_map or DEFAULT_ODOO_OPPORTUNITY_STAGE_MAP),
        strict_stages=True,
    )


def _partner_external_id(raw_partner: Any) -> str | None:
    if raw_partner is None or raw_partner is False:
        return None
    if isinstance(raw_partner, list | tuple) and raw_partner:
        return str(raw_partner[0]).strip() or None
    if isinstance(raw_partner, Mapping) and "id" in raw_partner:
        return str(raw_partner["id"]).strip() or None
    text = str(raw_partner).strip()
    return text or None


async def sync_opportunity_records(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    mappings: list[Mapping[str, Any]] | None = None,
    stage_map: Mapping[str, str] | None = None,
    translator: OdooTranslator | None = None,
) -> OpportunitySyncBatchResult:
    """Translate crm.lead opportunities; reject unmapped / raw stages loudly."""
    acl = translator or opportunity_translator(stage_map)
    maps = list(mappings or DEFAULT_OPPORTUNITY_MAPPINGS)
    out = OpportunitySyncBatchResult()

    for raw in records:
        if isinstance(raw, PullRecord):
            external_id = raw.external_id
            payload = raw.payload
            updated_at = raw.updated_at
        else:
            external_id = str(raw.get("id") or raw.get("external_id") or "")
            payload = dict(raw)
            updated_at = None
        # Skip Odoo leads that are not opportunities when type is present.
        lead_type = payload.get("type")
        if lead_type is not None and str(lead_type).strip() not in {"", "opportunity"}:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "not_opportunity",
                    "message": f"crm.lead type={lead_type!r} skipped (opportunity sync)",
                }
            )
            continue
        try:
            canonical = acl.translate(
                payload,
                mappings=maps,
                sync_run_id=sync_run_id,
                source_updated_at=updated_at,
            )
            stage = str(canonical.payload.get("stage") or "")
            if stage not in CANONICAL_OPPORTUNITY_STAGES:
                raise AclValidationError(
                    f"ACL rejected record: stage {stage!r} is not a canonical "
                    f"SalesOS opportunity stage (raw Odoo value forbidden)",
                    field="stage",
                )
            # Optional fields: map + normalize without making ACL require them.
            for internal, external in _OPTIONAL_OPPORTUNITY_EXTERNALS:
                if external in payload and payload.get(external) not in (None, False, ""):
                    canonical.payload[internal] = payload.get(external)
            extras = acl._normalize(
                {k: canonical.payload[k] for k in ("note", "currency", "name") if k in canonical.payload}
            )
            for key in ("note", "currency"):
                if key in extras:
                    canonical.payload[key] = extras[key]
            partner_raw = canonical.payload.get("partner_external_id")
            if partner_raw is None:
                partner_raw = payload.get("partner_id")
            partner_ext = _partner_external_id(partner_raw)
            canonical.payload["partner_external_id"] = partner_ext
            cur = canonical.payload.get("currency")
            if isinstance(cur, list | tuple) and len(cur) >= 2:
                canonical.payload["currency"] = str(cur[1]).strip()
            elif isinstance(cur, list | tuple) and cur:
                canonical.payload["currency"] = str(cur[0]).strip()
            out.synced.append(
                OpportunitySyncItem(
                    external_id=external_id or "unknown",
                    record=canonical,
                    partner_external_id=partner_ext,
                )
            )
        except AclValidationError as exc:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "malformed_data",
                    "message": str(exc),
                    "field": exc.field,
                }
            )
        except Exception as exc:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "unknown",
                    "message": str(exc),
                }
            )
    return out
