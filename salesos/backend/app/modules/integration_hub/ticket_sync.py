"""STORY-09-04 — helpdesk.ticket → SupportTicket (OBJ-019) sync.

Odoo helpdesk stages translated to canonical SalesOS ticket stages (no raw
passthrough). Description scrubbed via AI-GR-001 before any RAG-adjacent field.
No invented secrets. Not Production GO.
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
from intelligence.guardrails import scrub_pii_for_rag

# Canonical SupportTicket stages (DOM-019 Customer Success).
CANONICAL_TICKET_STAGES = frozenset(
    {
        "new",
        "in_progress",
        "on_hold",
        "solved",
        "cancelled",
    }
)

# Example Odoo helpdesk.stage → canonical map for certify/CI (not tenant secrets).
DEFAULT_ODOO_TICKET_STAGE_MAP: dict[str, str] = {
    "1": "new",
    "2": "in_progress",
    "3": "on_hold",
    "4": "solved",
    "5": "cancelled",
    "new": "new",
    "in_progress": "in_progress",
    "on_hold": "on_hold",
    "solved": "solved",
    "cancelled": "cancelled",
    "done": "solved",
    "closed": "solved",
}

DEFAULT_TICKET_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "name", "external": "name", "direction": "pull"},
    {"internal": "stage", "external": "stage_id", "direction": "pull"},
    {"internal": "priority", "external": "priority", "direction": "pull"},
    {"internal": "partner_external_id", "external": "partner_id", "direction": "pull"},
]

_OPTIONAL_TICKET_EXTERNALS: tuple[tuple[str, str], ...] = (
    ("description", "description"),
    ("assignee_external_id", "user_id"),
    ("sla_deadline", "sla_deadline"),
    ("ticket_type", "ticket_type"),
)


@dataclass
class SupportTicketItem:
    external_id: str
    record: CanonicalRecord
    partner_external_id: str | None = None


@dataclass
class TicketSyncBatchResult:
    synced: list[SupportTicketItem] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.synced) + len(self.failed)


def ticket_translator(
    stage_map: Mapping[str, str] | None = None,
) -> OdooTranslator:
    """ACL for SupportTicket — strict stage translation (no passthrough)."""
    return OdooTranslator(
        stage_map=dict(stage_map or DEFAULT_ODOO_TICKET_STAGE_MAP),
        strict_stages=True,
    )


def _many2one_id(raw: Any) -> str | None:
    if raw is None or raw is False:
        return None
    if isinstance(raw, list | tuple) and raw:
        return str(raw[0]).strip() or None
    if isinstance(raw, Mapping) and "id" in raw:
        return str(raw["id"]).strip() or None
    text = str(raw).strip()
    return text or None


async def sync_support_tickets(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    mappings: list[Mapping[str, Any]] | None = None,
    stage_map: Mapping[str, str] | None = None,
    translator: OdooTranslator | None = None,
) -> TicketSyncBatchResult:
    """Translate helpdesk.ticket rows into canonical SupportTicket projections."""
    acl = translator or ticket_translator(stage_map)
    maps = list(mappings or DEFAULT_TICKET_MAPPINGS)
    out = TicketSyncBatchResult()

    for raw in records:
        if isinstance(raw, PullRecord):
            external_id = raw.external_id
            payload = raw.payload
            updated_at = raw.updated_at
        else:
            external_id = str(raw.get("id") or raw.get("external_id") or "")
            payload = dict(raw)
            updated_at = None
        try:
            # Priority may be 0 / False — not a required string.
            active_maps = list(maps)
            pri = payload.get("priority")
            if pri is None or pri is False or (isinstance(pri, str) and not pri.strip()):
                active_maps = [
                    m
                    for m in active_maps
                    if not (isinstance(m, Mapping) and m.get("internal") == "priority")
                ]
            partner = payload.get("partner_id")
            if partner is None or partner is False:
                active_maps = [
                    m
                    for m in active_maps
                    if not (isinstance(m, Mapping) and m.get("internal") == "partner_external_id")
                ]
            canonical = acl.translate(
                payload,
                mappings=active_maps,
                sync_run_id=sync_run_id,
                source_updated_at=updated_at,
            )
            stage = str(canonical.payload.get("stage") or "")
            if stage not in CANONICAL_TICKET_STAGES:
                raise AclValidationError(
                    f"ACL rejected record: stage {stage!r} is not a canonical "
                    f"SupportTicket stage (raw Odoo value forbidden)",
                    field="stage",
                )
            for internal, external in _OPTIONAL_TICKET_EXTERNALS:
                if external in payload and payload.get(external) not in (None, False, ""):
                    canonical.payload[internal] = payload.get(external)
            partner_ext = _many2one_id(
                canonical.payload.get("partner_external_id") or payload.get("partner_id")
            )
            canonical.payload["partner_external_id"] = partner_ext
            assignee = _many2one_id(
                canonical.payload.get("assignee_external_id") or payload.get("user_id")
            )
            canonical.payload["assignee_external_id"] = assignee
            desc = canonical.payload.get("description") or payload.get("description")
            if desc is not None and desc is not False:
                scrub = scrub_pii_for_rag(str(desc))
                canonical.payload["description_raw"] = str(desc)
                canonical.payload["description"] = scrub.text
                canonical.payload["pii_redactions"] = dict(scrub.redactions)
            out.synced.append(
                SupportTicketItem(
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
