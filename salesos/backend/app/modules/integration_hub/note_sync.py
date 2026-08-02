"""STORY-09-03 — mail.message → InteractionNote / TimelineEvent + PII scrub.

Raw note body never reaches RAG; AI-GR-001 ``scrub_pii_for_rag`` produces
``rag_text``. No invented secrets. Not Production GO.
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
from intelligence.guardrails import PiiScrubResult, scrub_pii_for_rag

DEFAULT_NOTE_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "subject", "external": "subject", "direction": "pull"},
    {"internal": "body", "external": "body", "direction": "pull"},
]

_OPTIONAL_NOTE_EXTERNALS: tuple[tuple[str, str], ...] = (
    ("message_type", "message_type"),
    ("model", "model"),
    ("res_id", "res_id"),
    ("author_external_id", "author_id"),
    ("date", "date"),
)


@dataclass
class InteractionNoteItem:
    """Canonical InteractionNote / TimelineEvent projection (pre-persist)."""

    external_id: str
    record: CanonicalRecord
    rag_text: str
    scrub: PiiScrubResult
    timeline_event_type: str = "interaction_note"


@dataclass
class NoteSyncBatchResult:
    synced: list[InteractionNoteItem] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.synced) + len(self.failed)


def _author_external_id(raw: Any) -> str | None:
    if raw is None or raw is False:
        return None
    if isinstance(raw, list | tuple) and raw:
        return str(raw[0]).strip() or None
    if isinstance(raw, Mapping) and "id" in raw:
        return str(raw["id"]).strip() or None
    text = str(raw).strip()
    return text or None


async def sync_interaction_notes(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    mappings: list[Mapping[str, Any]] | None = None,
    translator: OdooTranslator | None = None,
) -> NoteSyncBatchResult:
    """Translate mail.message notes; scrub body before exposing RAG text."""
    acl = translator or OdooTranslator()
    maps = list(mappings or DEFAULT_NOTE_MAPPINGS)
    out = NoteSyncBatchResult()

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
            # Subject may be empty on chatter notes — drop from required maps.
            subj = payload.get("subject")
            has_subject = isinstance(subj, str) and bool(subj.strip())
            body_maps = (
                maps
                if has_subject
                else [
                    m
                    for m in maps
                    if not (isinstance(m, Mapping) and m.get("internal") == "subject")
                ]
            )
            canonical = acl.translate(
                payload,
                mappings=body_maps,
                sync_run_id=sync_run_id,
                source_updated_at=updated_at,
            )
            for internal, external in _OPTIONAL_NOTE_EXTERNALS:
                if external in payload and payload.get(external) not in (None, False, ""):
                    canonical.payload[internal] = payload.get(external)
            author_raw = canonical.payload.get("author_external_id")
            if author_raw is None:
                author_raw = payload.get("author_id")
            canonical.payload["author_external_id"] = _author_external_id(author_raw)

            raw_body = str(canonical.payload.get("body") or payload.get("body") or "")
            scrub = scrub_pii_for_rag(raw_body)
            # Persist both: raw for operator audit path; rag_text is RAG-only.
            canonical.payload["body_raw"] = raw_body
            canonical.payload["rag_text"] = scrub.text
            canonical.payload["pii_redactions"] = dict(scrub.redactions)
            # Never leave unscrubbed body as the RAG field.
            if canonical.payload.get("body") == raw_body:
                canonical.payload["body"] = scrub.text

            out.synced.append(
                InteractionNoteItem(
                    external_id=external_id or "unknown",
                    record=canonical,
                    rag_text=scrub.text,
                    scrub=scrub,
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
