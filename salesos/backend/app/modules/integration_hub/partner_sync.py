"""STORY-09-01 — res.partner pull → ACL → cr_number join batch.

Orchestrates OdooAdapter records into match/unlinked outcomes.
Does not invent secrets. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    OdooTranslator,
)
from app.modules.integration_hub.cr_number_join import (
    CompanyLookup,
    CrJoinResult,
    GoldenLookup,
    join_partner_by_cr_number,
)
from app.modules.integration_hub.types import PullRecord

DEFAULT_PARTNER_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "name", "external": "name", "direction": "pull"},
    {"internal": "email", "external": "email", "direction": "pull"},
    {"internal": "phone", "external": "phone", "direction": "pull"},
    {"internal": "cr_number", "external": "x_studio_cr_number", "direction": "pull"},
]


@dataclass
class PartnerSyncBatchResult:
    matched: list[CrJoinResult] = field(default_factory=list)
    unlinked: list[CrJoinResult] = field(default_factory=list)
    invalid: list[CrJoinResult] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.matched) + len(self.unlinked) + len(self.invalid) + len(self.failed)


async def sync_partner_records(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    lookup_company: CompanyLookup,
    lookup_golden: GoldenLookup | None = None,
    mappings: list[Mapping[str, Any]] | None = None,
    translator: OdooTranslator | None = None,
) -> PartnerSyncBatchResult:
    """Translate each partner and join by cr_number against company dataset."""
    acl = translator or OdooTranslator()
    maps = list(mappings or DEFAULT_PARTNER_MAPPINGS)
    out = PartnerSyncBatchResult()

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
            # Join uses raw/studio CR before ACL may rename fields.
            join = await join_partner_by_cr_number(
                external_id=external_id or "unknown",
                payload=payload,
                lookup_company=lookup_company,
                lookup_golden=lookup_golden,
            )
            # Still run ACL for matched/valid paths to prove mapping.
            if join.status != "invalid_cr":
                acl.translate(
                    payload,
                    mappings=maps,
                    sync_run_id=sync_run_id,
                    source_updated_at=updated_at,
                )
            if join.status == "matched":
                out.matched.append(join)
            elif join.status == "unlinked":
                out.unlinked.append(join)
            else:
                out.invalid.append(join)
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


def company_lookup_from_index(
    index: Mapping[str, Any],
) -> CompanyLookup:
    """Build async lookup from an in-memory cr→company map (staging dataset sim)."""

    async def _lookup(cr: str) -> Any | None:
        return index.get(cr)

    return _lookup
