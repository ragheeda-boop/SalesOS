"""STORY-09-01 — cr_number join to Company / Golden Record dataset.

Surfaces unlinked partners loudly (never silent skip). No new RLS.
Not Production GO.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

JoinStatus = Literal["matched", "unlinked", "invalid_cr"]

_CR_RE = re.compile(r"^\d{10}$")

CompanyLookup = Callable[[str], Awaitable[Any | None]]
GoldenLookup = Callable[[str], Awaitable[Any | None]]


@dataclass(frozen=True)
class CrJoinResult:
    status: JoinStatus
    cr_number: str | None
    external_id: str
    company_id: str | None = None
    golden_record_id: str | None = None
    message: str = ""


def extract_cr_number(payload: Mapping[str, Any]) -> str | None:
    """Prefer canonical ``cr_number``, else Odoo studio field."""
    for key in ("cr_number", "x_studio_cr_number", "x_cr"):
        raw = payload.get(key)
        if raw is None:
            continue
        digits = re.sub(r"\D", "", str(raw))
        if digits:
            return digits
    return None


def normalize_cr(cr: str | None) -> str | None:
    if cr is None:
        return None
    digits = re.sub(r"\D", "", str(cr))
    return digits or None


async def join_partner_by_cr_number(
    *,
    external_id: str,
    payload: Mapping[str, Any],
    lookup_company: CompanyLookup,
    lookup_golden: GoldenLookup | None = None,
) -> CrJoinResult:
    """Join a pulled partner to the 141k company dataset via cr_number."""
    cr = normalize_cr(extract_cr_number(payload))
    if not cr:
        return CrJoinResult(
            status="invalid_cr",
            cr_number=None,
            external_id=str(external_id),
            message="missing cr_number — unlinked (not silently skipped)",
        )
    if not _CR_RE.match(cr):
        return CrJoinResult(
            status="invalid_cr",
            cr_number=cr,
            external_id=str(external_id),
            message=f"cr_number {cr!r} must be 10 digits — unlinked",
        )

    company = await lookup_company(cr)
    if company is not None:
        return CrJoinResult(
            status="matched",
            cr_number=cr,
            external_id=str(external_id),
            company_id=_entity_id(company),
            message="matched company by cr_number",
        )

    if lookup_golden is not None:
        golden = await lookup_golden(cr)
        if golden is not None:
            return CrJoinResult(
                status="matched",
                cr_number=cr,
                external_id=str(external_id),
                golden_record_id=_entity_id(golden),
                message="matched golden_record by cr_number",
            )

    return CrJoinResult(
        status="unlinked",
        cr_number=cr,
        external_id=str(external_id),
        message="no company/golden_record for cr_number — unlinked badge candidate",
    )


def _entity_id(obj: Any) -> str | None:
    if isinstance(obj, Mapping):
        val = obj.get("id")
        return str(val) if val is not None else None
    val = getattr(obj, "id", None)
    return str(val) if val is not None else None
