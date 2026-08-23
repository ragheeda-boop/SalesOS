"""EvidencePack construction for the grounded ResearchAgent (Grounded Phase 1).

Retrieval contract:
- Strictly scoped to (tenant_id, company_id); name-based lookup is intentionally
  unsupported so entity confusion (e.g. same-name organisations) cannot occur.
- Every item carries source type/id, field/value, basis label and optional
  confidence so any claim made downstream is traceable.

PII policy:
- Contact names, emails, phones and mobiles NEVER leave the database layer.
  Only business-relevant metadata (positions, departments, primacy, counts)
  is exposed to the LLM.
- Exact opportunity monetary values are replaced with coarse bands; stage,
  status and probability pass through as-is.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

BASIS_SOURCE = "source"
BASIS_DERIVED = "derived"

FORBIDDEN_PROMPT_SUBSTRINGS = ("@",)  # cheap tripwire: no emails in prompts


@dataclass
class EvidenceItem:
    source_type: str  # company | opportunity | contact_metadata | timeline | signal
    source_id: str | None
    field: str
    value: str  # PII-free, already stringified
    basis: str = BASIS_SOURCE  # source | derived | inference
    confidence: float | None = None


@dataclass
class EvidencePack:
    tenant_id: str
    company_id: str
    found: bool = False
    items: list[EvidenceItem] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)

    def add(self, item: EvidenceItem) -> None:
        self.items.append(item)

    def to_prompt_block(self) -> str:
        lines = [
            f"SUBJECT company_id={self.company_id}",
            f"tenant_verified={'True' if self.found else 'False'}",
            "",
        ]
        for i, it in enumerate(self.items, 1):
            conf = (
                f" confidence={it.confidence:.2f}" if it.confidence is not None else ""
            )
            lines.append(
                f"[E{i}] ({it.basis}/{it.source_type}) {it.field} = {it.value}"
                f" (id={it.source_id or 'n/a'}{conf})"
            )
        if self.missing_data:
            lines.append("")
            lines.append("MISSING IN SALESOS: " + "; ".join(self.missing_data))
        return "\n".join(lines)


def value_band(value) -> str:
    """Coarse confidentiality band instead of an exact deal amount."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if v <= 0:
        return "zero"
    if v < 100_000:
        return "<100K"
    if v <= 1_000_000:
        return "100K-1M"
    return ">1M"


def contact_metadata_items(contacts) -> list[EvidenceItem]:
    """Business-only metadata from Contact rows. PII fields are dropped here."""
    positions: list[str] = []
    departments: list[str] = []
    primary = 0
    for c in contacts:
        pos = (getattr(c, "position", None) or getattr(c, "position_ar", None) or "").strip()
        if pos and pos.lower() not in {p.lower() for p in positions}:
            positions.append(pos[:60])
        dep = (getattr(c, "department", None) or "").strip()
        if dep and dep.lower() not in {d.lower() for d in departments}:
            departments.append(dep[:60])
        if getattr(c, "is_primary", False):
            primary += 1
    items: list[EvidenceItem] = [
        EvidenceItem("contact_metadata", None, "contacts_total", str(len(contacts)))
    ]
    if primary:
        items.append(EvidenceItem("contact_metadata", None, "primary_contacts", str(primary)))
    if positions:
        items.append(
            EvidenceItem("contact_metadata", None, "positions", ", ".join(positions))
        )
    if departments:
        items.append(
            EvidenceItem("contact_metadata", None, "departments", ", ".join(departments))
        )
    return items


def _safe_str(v, limit: int = 120) -> str:
    s = "" if v is None else str(v).strip()
    return s[:limit]


async def build_company_evidence(session_factory, tenant_id: str, company_id: str) -> EvidencePack:
    """Load every available SalesOS fact for (tenant_id, company_id).

    Returns an EvidencePack; never raises for business-level misses (missing
    company, empty relations) — those become missing_data entries so the agent
    can answer UNKNOWN deterministically.
    """
    pack = EvidencePack(tenant_id=str(tenant_id), company_id=str(company_id))

    try:
        cid = uuid.UUID(str(company_id))
        tid = uuid.UUID(str(tenant_id))
    except ValueError:
        pack.missing_data.append("company_or_tenant_id_not_valid_uuid")
        return pack

    # Lazy imports keep the agents layer free of app-level circular deps.
    from sqlalchemy import select, text as sql_text

    from app.modules.company.models import Company, Contact
    from domains.commercial.infrastructure.models import OpportunityModel

    async with session_factory() as db:
        # DEC-085: RLS policies are fail-closed on current_setting('app.tenant_id').
        # Pin the tenant GUC (transaction-local) or every SELECT returns zero rows.
        await db.execute(
            sql_text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": str(tid)},
        )
        row = (
            await db.execute(
                select(Company).where(Company.id == cid, Company.tenant_id == tid)
            )
        ).scalar_one_or_none()
        if row is None:
            pack.missing_data.append("company_record_not_found_for_tenant")
            return pack

        pack.found = True
        citems = [
            ("status", row.status),
            ("city", row.city),
            ("region", row.region),
            ("industry", row.industry),
            ("segment", getattr(row, "segment", None)),
            ("cr_type", row.cr_type),
            ("legal_form", row.legal_form),
            ("isic_description", row.isic_description),
            ("activity_code", row.activity_code),
            ("employees_count", row.employees_count),
            ("country", row.country),
        ]
        sid = str(row.id)
        for f, v in citems:
            if v not in (None, ""):
                pack.add(EvidenceItem("company", sid, f, _safe_str(v)))
        if row.incorporation_date:
            pack.add(
                EvidenceItem("company", sid, "incorporation_year", str(row.incorporation_date.year))
            )
        if not any(i.field != "status" for i in pack.items):
            pack.missing_data.append("company_profile_fields_sparse")

        opps = (
            (
                await db.execute(
                    select(OpportunityModel)
                    .where(
                        OpportunityModel.tenant_id == str(tid),
                        OpportunityModel.company_id == str(cid),
                    )
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )
        if not opps:
            pack.missing_data.append("opportunities")
        for o in opps:
            oid = str(o.id)
            pack.add(EvidenceItem("opportunity", oid, "name", _safe_str(o.name, 80)))
            pack.add(EvidenceItem("opportunity", oid, "stage", _safe_str(o.stage)))
            pack.add(EvidenceItem("opportunity", oid, "status", _safe_str(o.status)))
            pack.add(
                EvidenceItem(
                    "opportunity",
                    oid,
                    "probability",
                    f"{float(o.probability or 0):.0%}",
                )
            )
            pack.add(
                EvidenceItem(
                    "opportunity",
                    oid,
                    "value_band",
                    value_band(o.value),
                    basis=BASIS_DERIVED,
                )
            )

        contacts = (
            (
                await db.execute(
                    select(Contact).where(
                        Contact.tenant_id == tid, Contact.company_id == cid
                    )
                )
            )
            .scalars()
            .all()
        )
        if not contacts:
            pack.missing_data.append("contacts")
        for it in contact_metadata_items(contacts):
            pack.add(it)

        # Company mutation history lives in audit.audit_log (0001_baseline),
        # written by sdk.audit.AuditTrail — the same store the /360 timeline
        # renders. Reuse its query abstraction instead of hand-rolled SQL.
        from sdk.audit import AuditTrail

        events = await AuditTrail(db).query(
            tenant_id=str(tid), entity_type="company", entity_id=str(cid), limit=5
        )
        if not events:
            pack.missing_data.append("timeline_events")
        for ev in events:
            actor = "system" if not ev.get("performed_by") else "user"
            performed_at = ev.get("performed_at")
            when = (
                performed_at.date().isoformat()
                if hasattr(performed_at, "date")
                else ""
            )
            pack.add(
                EvidenceItem(
                    "timeline",
                    str(ev.get("id") or "") or None,
                    f"event:{ev.get('action')}",
                    f"actor={actor} at={when}",
                )
            )

        # Signals layer is optional (locally empty today); failure is honest.
        try:
            res = await db.execute(
                sql_text(
                    "SELECT signal_type, severity, status, confidence_score "
                    "FROM company_signals "
                    "WHERE tenant_id = :t AND company_id = :c LIMIT 5"
                ),
                {"t": str(tid), "c": str(cid)},
            )
            sig = res.all()
            if not sig:
                pack.missing_data.append("signals")
            for r in sig:
                value = f"severity={r[1]} status={r[2]} confidence={r[3]}"
                pack.add(EvidenceItem("signal", None, f"signal:{r[0]}", _safe_str(value)))
        except Exception:
            pack.missing_data.append("signals_layer_unavailable")

    return pack
