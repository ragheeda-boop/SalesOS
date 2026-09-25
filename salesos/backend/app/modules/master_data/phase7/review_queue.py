"""Phase 7-A — Review Queue Service.

Read-only exports + record-only disposition capture for review-queue tooling.

HARD LIMITS (enforced by design):
  - Writes ONLY to `md_review_queue_state` (the single permitted Phase 7-A table).
  - NO write to any Phase 6 table (source rows, global companies/people,
    identity classifications, review candidates, contact relationships,
    industry/quality/readiness history).
  - NO merge, NO CR promotion, NO classification/readiness change.
  - DB scope: reads allowed on the app's connected DB; the disposition WRITE
    is asserted to `salesos_test` only.
  - No Apollo / external API.

Dispositions are CAPTURE-ONLY: writing a disposition records intent; it never
triggers a merge, a CR promotion, or any classification change.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.modules.master_data.phase7.schemas import (
    MAUnresolvedDisposition,
    P1CandidateDisposition,
    P2SampleDisposition,
    P3PairDisposition,
    ReviewEvidence,
    ShortCRDisposition,
    TriageDisposition,
    _assert_text_pii_free,
)

# Queue types.
QUEUE_P3 = "P3_PAIR"
QUEUE_SHORT_CR = "SHORT_CR"
QUEUE_TRIAGE = "TRIAGE"
QUEUE_P1 = "P1_CANDIDATE"
QUEUE_P2_SAMPLE = "P2_SAMPLE"
QUEUE_MA_UNRESOLVED = "MA_UNRESOLVED"

# Disposition enums keyed by queue type (capture-only).
_DISPOSITIONS = {
    QUEUE_P3: {d.value for d in P3PairDisposition},
    QUEUE_SHORT_CR: {d.value for d in ShortCRDisposition},
    QUEUE_TRIAGE: {d.value for d in TriageDisposition},
    QUEUE_P1: {d.value for d in P1CandidateDisposition},
    QUEUE_P2_SAMPLE: {d.value for d in P2SampleDisposition},
    QUEUE_MA_UNRESOLVED: {d.value for d in MAUnresolvedDisposition},
}

P2_SAMPLE_SUBJECTS = {
    "P2:SALES_READY_WITH_REVIEW",
    "P2:ENRICHMENT_REQUIRED",
    "P2:ALL",
}

# CR separator regex (matches Phase 5 normalize_cr separators).
_CR_SEP_RE = re.compile(r"[;|،؛,]+")


# Phase 6 + Phase 7-A review data lives in `salesos_test` (the only DB the
# pipeline was permitted to write to). The app's request session is bound to
# the app DB (e.g. `salesos`, for auth/tenancy), which does NOT contain the
# md_* review tables. The review service therefore uses its own dedicated
# engine/session pointing at `salesos_test` so the read-only exports and the
# record-only disposition write reach the review data without ever writing to
# the app/production DB.
def _review_database_url() -> str:
    base = settings.resolved_database_url  # postgresql+asyncpg://user:pass@host:port/db
    # Replace the trailing database name with salesos_test.
    return re.sub(r"/([^/]*)$", "/salesos_test", base)


_review_engine = create_async_engine(
    _review_database_url(),
    echo=settings.debug,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=10,
    connect_args={"command_timeout": 10},
)
review_async_session = async_sessionmaker(_review_engine, class_=AsyncSession, expire_on_commit=False)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _split_multi(v: str | None) -> list[str]:
    if not v:
        return []
    return [t.strip() for t in _CR_SEP_RE.split(v) if t.strip()]


class ReviewQueueService:
    """Read-only review-queue queries + record-only disposition capture.

    The service binds to a `salesos_test` session (review_async_session) so it
    reaches the Phase 6 + Phase 7-A review tables. Auth/tenancy stays on the
    app DB. A session can be injected for tests.
    """

    def __init__(self, session: AsyncSession | None = None, tenant_id: str | None = None, *,
                 unsafe_allow_test_subjects: bool = False):
        self.session = session or review_async_session()
        self.tenant_id = tenant_id
        self._owns_session = session is None
        # Report 116 W1: explicit, dependency-injected test flag replacing the
        # `subject_key.startswith("test:")` backdoor that used to live in
        # production code and would fire for ANY caller, not just tests.
        # Default False: a service built the normal way (API router, scripts)
        # can never activate the bypass regardless of what subject_key a
        # caller sends. Only test fixtures construct the service with this
        # flag set.
        self._unsafe_allow_test_subjects = unsafe_allow_test_subjects

    # ── DB scope assertion ────────────────────────────────────────────────

    async def _current_db(self) -> str:
        db = await self.session.execute(text("SELECT current_database()"))
        db_name = (db.scalar() or "").strip()
        if db_name != "salesos_test":
            raise RuntimeError(
                f"REFUSING: Phase 7-A review reads are restricted to salesos_test, "
                f"connected to {db_name!r}"
            )
        return db_name

    async def _assert_write_db(self) -> None:
        """Disposition capture (the only Phase 7-A write) must target salesos_test."""
        await self._current_db()

    # ── P3 pair read (from seeded md_review_queue_state) ───────────────────

    async def list_p3_pairs(self, *, status: str | None = None,
                            batch: str | None = None,
                            offset: int = 0, limit: int = 500) -> tuple[list[dict[str, Any]], int]:
        """Read-only list of P3 pairs from the seeded state table.

        batch='priority' — PO 2026-09-09 D3 domain-equal first human batch.
        batch='remainder' — other pending pairs (no D3 priority note).
        Default list is unchanged (all P3 rows) so existing count/export tests hold.
        """
        await self._current_db()
        where = "WHERE q.queue_type = :q"
        params: dict[str, Any] = {"q": QUEUE_P3, "offset": offset, "limit": limit}
        if status:
            where += " AND q.status = :status"
            params["status"] = status
        if batch == "priority":
            where += " AND q.notes LIKE :note"
            params["note"] = "%PHASE7A_PO_DECISION_2026-09-09 D3%"
        elif batch == "remainder":
            where += " AND (q.notes IS NULL OR q.notes NOT LIKE :note)"
            params["note"] = "%PHASE7A_PO_DECISION_2026-09-09 D3%"
        total = await self.session.execute(
            text(f"SELECT COUNT(*) FROM md_review_queue_state q {where}"),
            {k: v for k, v in params.items() if k not in ("offset", "limit")},
        )
        count = total.scalar() or 0
        rows = await self.session.execute(
            text(
                f"SELECT q.id, q.subject_key, q.global_company_id, q.global_company_id_b, "
                f"q.evidence_ref, q.status, q.disposition, q.reviewer, q.reviewed_at, q.notes, "
                f"a.canonical_name AS name_a, a.domain AS domain_a, a.cr_number AS cr_a, "
                f"b.canonical_name AS name_b, b.domain AS domain_b, b.cr_number AS cr_b "
                f"FROM md_review_queue_state q "
                f"LEFT JOIN md_global_companies a ON a.id = q.global_company_id "
                f"LEFT JOIN md_global_companies b ON b.id = q.global_company_id_b "
                f"{where} ORDER BY q.created_at LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        items = [self._row_to_dict(r) for r in rows.mappings()]
        return items, count

    async def get_p3_count(self) -> int:
        await self._current_db()
        rows = await self.session.execute(
            text("SELECT COUNT(*) FROM md_review_queue_state WHERE queue_type = :q"), {"q": QUEUE_P3}
        )
        return rows.scalar() or 0

    # ── Short-CR read (36 accounts) ───────────────────────────────────────

    async def list_short_cr(self) -> list[dict[str, Any]]:
        """Read-only enumeration of the 36 suspicious short-CR accounts.

        Starts from the 36 curated SHORT_CR queue entries and uses the
        (source_id, source_record_id) index to fetch each raw payload. The old
        payload-wide semicolon scan could time out while other queue panels
        loaded concurrently. No write.
        """
        await self._current_db()
        rows = await self.session.execute(
            text(
                "SELECT rq.subject_key AS ma, "
                "       ms.raw_payload->>'CR_Numbers' AS cr_number, "
                "       rq.global_company_id AS company_id "
                "FROM md_review_queue_state rq "
                "JOIN md_source_rows ms "
                "  ON ms.source_id = 'muhide_master_accounts' "
                " AND ms.source_record_id = rq.subject_key "
                "WHERE rq.queue_type = :queue_type "
                "ORDER BY rq.subject_key"
            ),
            {"queue_type": QUEUE_SHORT_CR},
        )
        items = []
        for r in rows.mappings():
            tokens = _split_multi(r["cr_number"])
            valid, rejected = self._partition_cr_tokens(tokens)
            items.append({
                "master_account_id": r["ma"],
                "global_company_id": str(r["company_id"]) if r["company_id"] else None,
                "cr_number_raw": r["cr_number"],
                "valid_cr_count": len(valid),
                "rejected_tokens": rejected,
            })
        return items

    def _partition_cr_tokens(self, tokens: list[str]) -> tuple[list[str], list[str]]:
        """Split CR tokens into valid (>=8 digits) vs rejected (SUSPICIOUS_SHORT).

        Mirrors the Phase 5/6 normalize_cr behavior: a token is a valid CR only
        if it is all digits with >=8 digits; shorter tokens are SUSPICIOUS_SHORT
        (never promoted here).
        """
        valid, rejected = [], []
        for t in tokens:
            digits = re.sub(r"[^0-9]", "", t)
            if digits and len(digits) >= 8:
                valid.append(digits)
            else:
                rejected.append(t)
        return valid, rejected

    # ── P1/P2 (and P3-account) triage read ────────────────────────────────

    async def list_triage_candidates(self, *, candidate_type: str | None = None,
                                     offset: int = 0, limit: int = 500) -> tuple[list[dict[str, Any]], int]:
        """Read-only list of review candidates (P1/P2/P3-account) from md_review_candidates.

        Does NOT write. status/disposition shown is the existing candidate
        field; disposition capture goes to md_review_queue_state (see
        record_disposition).
        """
        await self._current_db()
        from app.modules.master_data.phase6.pipeline import ACTIVE_CLASSIFICATION_VERSION

        where = "WHERE rc.status <> 'superseded'"
        params: dict[str, Any] = {
            "offset": offset, "limit": limit, "version": ACTIVE_CLASSIFICATION_VERSION,
        }
        if candidate_type:
            where += " AND rc.candidate_type = :ct"
            params["ct"] = candidate_type
        total = await self.session.execute(
            text(f"SELECT COUNT(*) FROM md_review_candidates rc {where}"), params
        )
        count = total.scalar() or 0
        rows = await self.session.execute(
            text(
                f"SELECT rc.global_entity_id, rc.candidate_type, rc.reason, rc.status, rc.decision, "
                f"       ic.identity_state "
                f"FROM md_review_candidates rc "
                f"LEFT JOIN md_identity_classifications ic ON ic.global_entity_id = rc.global_entity_id "
                f"  AND ic.classification_version = :version "
                f"{where} ORDER BY rc.created_at LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        items = [{
            "global_company_id": str(r["global_entity_id"]),
            "candidate_type": r["candidate_type"],
            "reason": r["reason"],
            "identity_state": r["identity_state"],
            "status": r["status"],
            "disposition": r["decision"],
        } for r in rows.mappings()]
        return items, count

    async def get_triage_counts(self) -> dict[str, int]:
        """Read-only per-type/reason counts for the triage queues."""
        await self._current_db()
        rows = await self.session.execute(
            text(
                "SELECT candidate_type, reason, COUNT(*) AS c FROM md_review_candidates "
                "WHERE status <> 'superseded' GROUP BY candidate_type, reason ORDER BY candidate_type, reason"
            )
        )
        out: dict[str, int] = {}
        for r in rows.mappings():
            out[f"{r['candidate_type']}:{r['reason']}"] = r["c"]
        return out

    # ── Sales usability under PO decisions A2/A3 (read-only) ──────────────

    async def get_sales_usability_summary(self) -> dict[str, Any]:
        from .usability import usability_summary

        await self._current_db()
        return await usability_summary(self.session)

    async def list_sales_usability(self, *, usable: bool | None, blocker: str | None,
                                   offset: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        from .usability import list_accounts

        await self._current_db()
        return await list_accounts(self.session, usable=usable, blocker=blocker,
                                   offset=offset, limit=limit)

    # ── Record-only disposition capture ───────────────────────────────────

    async def _resolve_company_link(
        self, queue_type: str, subject_key: str
    ) -> tuple[str | None, str]:
        """Resolve a queue subject to a real Global Company.

        Returns `(global_company_id, default_linkage_status)`.

        `global_company_id` is None when the subject is not company-shaped
        (a P2 stratum, a Global Person) or when the translation is genuinely
        unrecoverable (P3 indexes an external file that was never ingested).
        Nothing is ever guessed or borrowed.

        The guard is deliberately queue-specific: only subjects that ARE a
        company (P1 Global Company UUID, SHORT_CR MA id) are refused when they
        fail to resolve, because recording their disposition would otherwise
        leave a dangling key with no accountable company.
        """
        if self._unsafe_allow_test_subjects and subject_key.startswith("test:"):
            return None, "SUBJECT_NOT_A_COMPANY"

        if queue_type == QUEUE_P1:
            try:
                uuid.UUID(subject_key)
            except ValueError as exc:
                raise ValueError("P1 subject_key must be a Global Company UUID") from exc
            candidate = await self.session.execute(
                text(
                    "SELECT 1 FROM md_review_candidates "
                    "WHERE global_entity_id = CAST(:gid AS uuid) AND candidate_type = 'P1' "
                    "AND status <> 'superseded'"
                ),
                {"gid": subject_key},
            )
            if candidate.first() is None:
                raise ValueError("P1 subject_key is not a pending P1 candidate")
            # A P1 subject IS the Global Company. Assert it is a real company
            # row before writing it into the linkage column.
            real = await self.session.execute(
                text("SELECT 1 FROM md_global_companies WHERE id = CAST(:gid AS uuid)"),
                {"gid": subject_key},
            )
            if real.first() is None:
                raise ValueError("P1 subject_key is not a real Global Company")
            return subject_key, "RESOLVED"

        if queue_type == QUEUE_SHORT_CR:
            # MA-XXXXXXX -> Global Company via the authoritative legacy crosswalk.
            if not re.fullmatch(r"MA-\d{7}", subject_key):
                raise ValueError("SHORT_CR subject_key must be a MA-XXXXXXX master account id")
            link = await self.session.execute(
                text(
                    "SELECT global_entity_id::text AS gid FROM md_legacy_id_mappings "
                    "WHERE legacy_id_type = 'LEGACY_MUHIDE_MA_ID' AND legacy_id = :ma"
                ),
                {"ma": subject_key},
            )
            resolved = link.scalar()
            if not resolved:
                raise ValueError(
                    f"SHORT_CR subject_key {subject_key!r} does not resolve to a real "
                    "Global Company via the MA crosswalk"
                )
            return str(resolved), "RESOLVED"

        if queue_type == QUEUE_P3:
            # P3 subject_key is "row_a:row_b" indexing an external MUHIDE
            # candidates file that was never ingested as a source file, so the
            # row -> Global Company translation is not recoverable here. Reuse
            # whatever linkage a prior pass proved and otherwise record the
            # gap; never invent an ID. See report 114.
            existing = await self.session.execute(
                text(
                    "SELECT global_company_id::text AS gid FROM md_review_queue_state "
                    "WHERE queue_type = :q AND subject_key = :sk"
                ),
                {"q": queue_type, "sk": subject_key},
            )
            resolved = existing.scalar()
            if resolved:
                return str(resolved), "RESOLVED"
            return None, "SOURCE_ROWS_UNRESOLVED"

        return None, "SUBJECT_NOT_A_COMPANY"

    async def record_disposition(self, *, queue_type: str, subject_key: str,
                                 disposition: str, reviewer: str,
                                 notes: str | None = None,
                                 evidence: dict[str, Any] | ReviewEvidence) -> dict[str, Any]:
        """CAPTURE a review disposition into md_review_queue_state.

        This is record-only: it updates the state row's status/disposition and
        NEVER triggers a merge, CR promotion, or classification change. It is
        idempotent on (queue_type, subject_key).

        `evidence` is REQUIRED and typed (report 116 W1 — an intentional
        API-breaking change from the prior optional free-form dict). A plain
        dict is accepted for callers that build one directly (scripts, older
        tests) and is validated against `ReviewEvidence` here — this is the
        single enforcement point for both the HTTP API and direct script/test
        callers, so neither path can bypass the required-`reason` / typed-
        field / PII-impossible-by-construction guarantee. `global_company_id`
        is resolved from the subject itself and only ever asserted when the
        subject resolves to a REAL Global Company; a subject that cannot be
        resolved is captured with a NULL `global_company_id` plus
        `evidence_ref.linkage_status`, never with a guessed or borrowed ID.
        """
        await self._assert_write_db()
        if queue_type not in _DISPOSITIONS:
            raise ValueError(f"unknown queue_type: {queue_type}")
        if disposition not in _DISPOSITIONS[queue_type]:
            raise ValueError(f"invalid disposition {disposition!r} for {queue_type}")
        if isinstance(evidence, ReviewEvidence):
            typed_evidence = evidence
        elif isinstance(evidence, dict):
            typed_evidence = ReviewEvidence.model_validate(evidence)
        else:
            raise ValueError("evidence must be a ReviewEvidence or an equivalent dict")
        if notes:
            _assert_text_pii_free(notes, field="notes")
        if queue_type == QUEUE_P2_SAMPLE and not (
            subject_key in P2_SAMPLE_SUBJECTS
            or (self._unsafe_allow_test_subjects and subject_key.startswith("test:"))
        ):
            raise ValueError("P2 sample subject_key must name an approved stratum")
        if queue_type == QUEUE_P2_SAMPLE and not (notes or "").strip():
            raise ValueError("P2 sample acceptance requires review notes and evidence")
        if queue_type == QUEUE_MA_UNRESOLVED:
            if not subject_key.startswith("GP-"):
                raise ValueError("MA unresolved subject_key must be a v0.7 Global Person ID")
            if not (notes or "").strip():
                raise ValueError("MA unresolved capture requires candidate evidence notes")
            source = await self.session.execute(
                text(
                    "SELECT 1 FROM md_source_rows "
                    "WHERE source_id = 'muhide_contacts_v07' AND source_record_id = :gp"
                ),
                {"gp": subject_key},
            )
            if source.first() is None:
                raise ValueError("MA unresolved subject_key is not a v0.7 contact")
        global_company_id, default_linkage = await self._resolve_company_link(
            queue_type, subject_key
        )

        evidence_ref = typed_evidence.model_dump(exclude_none=True)
        evidence_ref.setdefault("linkage_status", default_linkage)

        row_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{queue_type}:{subject_key}"))
        now = datetime.now(UTC)
        await self.session.execute(
            text(
                "INSERT INTO md_review_queue_state "
                "(id, queue_type, subject_key, global_company_id, evidence_ref, status, "
                " disposition, reviewer, reviewed_at, notes) "
                "VALUES (:id, :q, :sk, CAST(:gid AS uuid), CAST(:ev AS JSONB), 'dispositioned', "
                "        :disp, :reviewer, :now, :notes) "
                "ON CONFLICT (queue_type, subject_key) DO UPDATE "
                "SET status = 'dispositioned', disposition = :disp, "
                "    reviewer = :reviewer, reviewed_at = :now, notes = :notes, "
                "    global_company_id = COALESCE(EXCLUDED.global_company_id, "
                "                                md_review_queue_state.global_company_id), "
                "    evidence_ref = jsonb_set("
                "        md_review_queue_state.evidence_ref || EXCLUDED.evidence_ref, "
                "        '{linkage_status}', "
                "        COALESCE(md_review_queue_state.evidence_ref -> 'linkage_status', "
                "                 EXCLUDED.evidence_ref -> 'linkage_status'), true)"
            ),
            {
                "id": row_id, "q": queue_type, "sk": subject_key, "gid": global_company_id,
                "ev": json.dumps(evidence_ref, default=str),
                "disp": disposition, "reviewer": reviewer, "now": now, "notes": notes,
            },
        )
        await self.session.commit()

        # Read back the captured row (idempotent).
        row = await self.session.execute(
            text(
                "SELECT id, queue_type, subject_key, global_company_id, evidence_ref, status, "
                "       disposition, reviewer, reviewed_at, notes FROM md_review_queue_state "
                "WHERE queue_type = :q AND subject_key = :sk"
            ),
            {"q": queue_type, "sk": subject_key},
        )
        m = row.mappings().first()
        stored_evidence = m["evidence_ref"]
        if isinstance(stored_evidence, str):
            try:
                stored_evidence = json.loads(stored_evidence)
            except json.JSONDecodeError:
                stored_evidence = {"raw": stored_evidence}
        return {
            "id": str(m["id"]),
            "queue_type": m["queue_type"],
            "subject_key": m["subject_key"],
            "global_company_id": str(m["global_company_id"]) if m["global_company_id"] else None,
            "evidence_ref": stored_evidence,
            "status": m["status"],
            "disposition": m["disposition"],
            "reviewer": m["reviewer"],
            "reviewed_at": m["reviewed_at"],
            "notes": m["notes"],
        }

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(r: Any) -> dict[str, Any]:
        evidence = r["evidence_ref"]
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except json.JSONDecodeError:
                evidence = {"raw": evidence}
        keys = r.keys()
        return {
            "id": str(r["id"]) if r["id"] else None,
            "subject_key": r["subject_key"],
            "global_company_id": str(r["global_company_id"]) if r["global_company_id"] else None,
            "global_company_id_b": str(r["global_company_id_b"]) if r["global_company_id_b"] else None,
            "evidence_ref": evidence,
            "status": r["status"],
            "disposition": r["disposition"],
            "notes": r["notes"] if "notes" in keys else None,
            "name_a": r["name_a"] if "name_a" in keys else None,
            "domain_a": r["domain_a"] if "domain_a" in keys else None,
            "cr_a": r["cr_a"] if "cr_a" in keys else None,
            "name_b": r["name_b"] if "name_b" in keys else None,
            "domain_b": r["domain_b"] if "domain_b" in keys else None,
            "cr_b": r["cr_b"] if "cr_b" in keys else None,
        }
