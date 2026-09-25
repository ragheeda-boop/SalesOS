"""Integration tests for Phase 7-A review-queue tooling (salesos_test, read-only +
record-only disposition capture)."""

import json

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.modules.master_data.phase7.review_queue import ReviewQueueService
from app.modules.master_data.phase7.schemas import (
    P3PairDisposition,
    ShortCRDisposition,
    TriageDisposition,
)

PG_URL = "postgresql+asyncpg://salesos:salesos_dev_password@localhost:5432/salesos_test"

# Marker for the synthetic dangling P1 candidate used by the 1.3 guard test.
# md_review_candidates is unique on (global_entity_id, candidate_type, reason),
# so a dedicated reason string both isolates and cleans up the fixture.
_TEST_CANDIDATE_REASON = "test: phase7a dangling subject with no company row"

# Evidence-marker values for the additive-merge test.
_FIRST_PASS, _SECOND_PASS = 1, 2

# Phase 6 tables that must remain unchanged.
PHASE6_TABLES = [
    "md_source_rows", "md_global_companies", "md_global_people",
    "md_identity_classifications", "md_review_candidates", "md_contact_relationships",
    "md_industry_normalization", "md_quality_score_history", "md_sales_readiness_history",
    "md_p0_dispositions", "md_entity_merge_history", "md_entity_conflicts",
]


@pytest.fixture
async def session():
    engine = create_async_engine(PG_URL)
    async with AsyncSession(engine) as s:
        db = (await s.execute(text("SELECT current_database()"))).scalar()
        assert db == "salesos_test", f"must run on salesos_test, got {db}"
        yield s
    await engine.dispose()


class TestPhase7AQueueReads:
    """Read-only queue counts (2,661 P3 / 36 short-CR / P1-P2 triage)."""

    @pytest.mark.asyncio
    async def test_p3_pair_count_is_2661(self, session):
        svc = ReviewQueueService(session)
        count = await svc.get_p3_count()
        assert count == 2661

    @pytest.mark.asyncio
    async def test_p3_pairs_reference_real_companies(self, session):
        svc = ReviewQueueService(session)
        items, total = await svc.list_p3_pairs(offset=0, limit=1000)
        assert total == 2661
        assert items
        for it in items:
            for gid in (it["global_company_id"], it["global_company_id_b"]):
                if gid:
                    c = await session.execute(
                        text("SELECT COUNT(*) FROM md_global_companies WHERE id = :g"), {"g": gid}
                    )
                    assert c.scalar() == 1, f"{gid} not a real company"

    @pytest.mark.asyncio
    async def test_short_cr_count_is_36(self, session):
        svc = ReviewQueueService(session)
        rows = await svc.list_short_cr()
        assert len(rows) == 36
        for r in rows:
            assert r["cr_number_raw"].count(";") >= 1

    @pytest.mark.asyncio
    async def test_p1_triage_count(self, session):
        svc = ReviewQueueService(session)
        items, total = await svc.list_triage_candidates(candidate_type="P1", offset=0, limit=10)
        assert total == 6249  # OPTION_C_1+NCNP+DS5+LV+CR (report 110)
        counts = await svc.get_triage_counts()
        assert counts["P1:CORROBORATION_REVIEW"] == 5903
        assert counts["P1:FIELD_CONFLICT_REVIEW"] == 234
        assert counts["P1:WEAK_IDENTITY_REVIEW"] == 112

    @pytest.mark.asyncio
    async def test_p2_triage_count(self, session):
        svc = ReviewQueueService(session)
        counts = await svc.get_triage_counts()
        assert counts["P2:PRIORITIZATION_PP2"] == 33654
        items, total = await svc.list_triage_candidates(candidate_type="P2", offset=0, limit=10)
        assert total == 33654


class TestPhase7ARecordOnly:
    """Capture-only: dispositions record intent but never change Phase 6 data.

    Each test uses "test:" prefixed subject keys and cleans them up in `finally`
    so the seeded population (2,661 P3 pairs) is never polluted.
    """

    @pytest.mark.asyncio
    async def test_no_phase6_change_after_disposition(self, session):
        svc = ReviewQueueService(session)
        keys = [
            ("P3_PAIR", "test:pair:nophase6change"),
            ("SHORT_CR", "test:short:nocrpromo"),
            ("TRIAGE", "test:triage:confirm"),
        ]
        before = {}
        for t in PHASE6_TABLES:
            c = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
            before[t] = c.scalar()
        try:
            for qt, sk in keys:
                await svc.record_disposition(
                    queue_type=qt, subject_key=sk,
                    disposition=_valid_disposition(qt), reviewer="test", notes="record-only",
                )
            after = {}
            for t in PHASE6_TABLES:
                c = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
                after[t] = c.scalar()
            assert before == after, "Phase 6 row counts changed after disposition capture"
        finally:
            await _cleanup_test_rows(session, keys)

    @pytest.mark.asyncio
    async def test_disposition_capture_only_in_state_table(self, session):
        svc = ReviewQueueService(session)
        import pytest as _pt
        with _pt.raises(ValueError):
            await svc.record_disposition(
                queue_type="P3_PAIR", subject_key="test:invalid:disp",
                disposition="AUTO_MERGE", reviewer="test",
            )
        assert "AUTO_MERGE" not in {d.value for d in P3PairDisposition}

    @pytest.mark.asyncio
    async def test_disposition_uses_real_company_context(self, session):
        svc = ReviewQueueService(session)
        keys = [("TRIAGE", "test:realcompany:review")]
        try:
            res = await svc.record_disposition(
                queue_type="TRIAGE", subject_key=keys[0][1],
                disposition="REVIEW", reviewer="test", notes="real-company check",
            )
            assert res["queue_type"] == "TRIAGE"
            assert res["status"] == "dispositioned"
        finally:
            await _cleanup_test_rows(session, keys)

    @pytest.mark.asyncio
    async def test_state_table_idempotency(self, session):
        svc = ReviewQueueService(session)
        key = ("P3_PAIR", "test:idempotent:pair")
        try:
            await svc.record_disposition(
                queue_type="P3_PAIR", subject_key=key[1], disposition="MATCH", reviewer="a"
            )
            await svc.record_disposition(
                queue_type="P3_PAIR", subject_key=key[1], disposition="MATCH", reviewer="b"
            )
            count = await session.execute(
                text("SELECT COUNT(*) FROM md_review_queue_state WHERE queue_type='P3_PAIR' AND subject_key=:k"),
                {"k": key[1]},
            )
            assert count.scalar() == 1
        finally:
            await _cleanup_test_rows(session, [key])

    @pytest.mark.asyncio
    async def test_p2_sample_capture_is_record_only(self, session):
        svc = ReviewQueueService(session)
        keys = [("P2_SAMPLE", "P2:SALES_READY_WITH_REVIEW")]
        existing = (
            await session.execute(
                text(
                    "SELECT id, status, disposition, reviewer, reviewed_at, notes, "
                    "global_company_id::text AS global_company_id, "
                    "global_company_id_b::text AS global_company_id_b, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ),
                {"q": keys[0][0], "k": keys[0][1]},
            )
        ).mappings().first()
        before = {}
        for table in PHASE6_TABLES:
            before[table] = (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
        try:
            result = await svc.record_disposition(
                queue_type="P2_SAMPLE",
                subject_key=keys[0][1],
                disposition="ACCEPT_SAMPLE",
                reviewer="test-p2-reviewer",
                notes="0.00% observed material error; sample hash verified.",
            )
            assert result["status"] == "dispositioned"
            assert result["disposition"] == "ACCEPT_SAMPLE"
            after = {}
            for table in PHASE6_TABLES:
                after[table] = (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
            assert before == after
        finally:
            await _cleanup_test_rows(session, keys, preserve={keys[0]: existing})

    @pytest.mark.asyncio
    async def test_p1_capture_requires_real_candidate_uuid(self, session):
        svc = ReviewQueueService(session)
        with pytest.raises(ValueError, match="Global Company UUID"):
            await svc.record_disposition(
                queue_type="P1_CANDIDATE",
                subject_key="not-a-uuid",
                disposition="REVIEW",
                reviewer="test",
            )

    @pytest.mark.asyncio
    async def test_p2_capture_rejects_unknown_stratum(self, session):
        svc = ReviewQueueService(session)
        with pytest.raises(ValueError, match="approved stratum"):
            await svc.record_disposition(
                queue_type="P2_SAMPLE",
                subject_key="P2:UNKNOWN",
                disposition="ACCEPT_SAMPLE",
                reviewer="test",
                notes="evidence",
            )

    @pytest.mark.asyncio
    async def test_ma_unresolved_capture_is_record_only(self, session):
        svc = ReviewQueueService(session)
        key = ("MA_UNRESOLVED", "GP-0000001")
        existing = (
            await session.execute(
                text(
                    "SELECT status, disposition, reviewer, reviewed_at, notes, "
                    "global_company_id::text AS global_company_id, "
                    "global_company_id_b::text AS global_company_id_b, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ), {"q": key[0], "k": key[1]}
            )
        ).mappings().first()
        try:
            result = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="CONFIRM_EXACT",
                reviewer="test-ma-reviewer", notes="candidate evidence; proposal only",
            )
            assert result["status"] == "dispositioned"
            assert result["disposition"] == "CONFIRM_EXACT"
        finally:
            await _cleanup_test_rows(session, [key], preserve={key: existing})


class TestQueueLinkageWriteThrough:
    """1.1 — a disposition carries canonical identity + structured evidence.

    `global_company_id` is resolved from the SUBJECT and only asserted when it
    maps to a real md_global_companies row. Nothing is ever invented.
    """

    @pytest.mark.asyncio
    async def test_p1_capture_writes_real_global_company_and_evidence(self, session):
        svc = ReviewQueueService(session)
        gid = (
            await session.execute(
                text(
                    "SELECT global_entity_id::text FROM md_review_candidates "
                    "WHERE candidate_type='P1' AND status <> 'superseded' LIMIT 1"
                )
            )
        ).scalar()
        assert gid, "need at least one pending P1 candidate"
        key = ("P1_CANDIDATE", gid)
        try:
            res = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="REVIEW",
                reviewer="test-linkage",
                notes="linkage write-through",
                evidence={"reason": "corroboration", "reviewed_via": "workbook"},
            )
            # 1.1: canonical identity is persisted, not just returned.
            assert res["global_company_id"] == gid
            row = await session.execute(
                text(
                    "SELECT global_company_id::text AS gid, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ),
                {"q": key[0], "k": key[1]},
            )
            m = row.mappings().one()
            assert m["gid"] == gid, "global_company_id was not persisted"
            assert m["evidence_ref"]["reason"] == "corroboration"
            assert m["evidence_ref"]["reviewed_via"] == "workbook"
            assert m["evidence_ref"]["linkage_status"] == "RESOLVED"
        finally:
            await _cleanup_test_rows(session, [key])

    @pytest.mark.asyncio
    async def test_short_cr_capture_links_via_legacy_crosswalk(self, session):
        svc = ReviewQueueService(session)
        rows = await svc.list_short_cr()
        target = next(r for r in rows if r["global_company_id"])
        key = ("SHORT_CR", target["master_account_id"])
        existing = (
            await session.execute(
                text(
                    "SELECT status, disposition, reviewer, reviewed_at, notes, "
                    "global_company_id::text AS global_company_id, "
                    "global_company_id_b::text AS global_company_id_b, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ),
                {"q": key[0], "k": key[1]},
            )
        ).mappings().first()
        try:
            res = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1],
                disposition="UNRESOLVED_ESCALATE", reviewer="test-cr-linkage",
                notes="short-CR crosswalk check",
                evidence={"cr_class": "SEPARATOR_LIST", "valid_cr_count": 1},
            )
            assert res["global_company_id"] == target["global_company_id"]
            assert res["evidence_ref"]["cr_class"] == "SEPARATOR_LIST"
            assert res["evidence_ref"]["linkage_status"] == "RESOLVED"
        finally:
            await _cleanup_test_rows(session, [key], preserve={key: existing})

    @pytest.mark.asyncio
    async def test_p3_capture_never_invents_company_id(self, session):
        """P3 subject_key indexes an un-ingested external file, so linkage stays
        NULL and the gap is recorded instead of guessed (report 114)."""
        svc = ReviewQueueService(session)
        # Real "rowA:rowB" shape, deliberately not present in the state table.
        key = ("P3_PAIR", "999999:888888")
        try:
            res = await svc.record_disposition(
                queue_type="P3_PAIR", subject_key=key[1], disposition="ESCALATE",
                reviewer="test-p3-linkage", notes="no source rows for pair sides",
                evidence={"pair_id": "FZ-TEST-999999-888888", "evidence_type": "FUZZY"},
            )
            assert res["global_company_id"] is None, "P3 must not fabricate a company id"
            assert res["evidence_ref"]["linkage_status"] == "SOURCE_ROWS_UNRESOLVED"
            assert res["evidence_ref"]["pair_id"] == "FZ-TEST-999999-888888"
        finally:
            await _cleanup_test_rows(session, [key])

    @pytest.mark.asyncio
    async def test_p3_recapture_preserves_precise_linkage_status(self, session):
        """Re-capturing a P3 row must not downgrade its backfilled linkage
        label (COMPLETE / MISSING_SIDE_B / MISSING_BOTH)."""
        svc = ReviewQueueService(session)
        row = (
            await session.execute(
                text(
                    "SELECT subject_key, evidence_ref FROM md_review_queue_state "
                    "WHERE queue_type='P3_PAIR' AND global_company_id_b IS NULL "
                    "AND evidence_ref ->> 'linkage_status' = 'MISSING_SIDE_B' LIMIT 1"
                )
            )
        ).mappings().first()
        assert row, "need a MISSING_SIDE_B P3 row"
        key = ("P3_PAIR", row["subject_key"])
        existing = (
            await session.execute(
                text(
                    "SELECT status, disposition, reviewer, reviewed_at, notes, "
                    "global_company_id::text AS global_company_id, "
                    "global_company_id_b::text AS global_company_id_b, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ),
                {"q": key[0], "k": key[1]},
            )
        ).mappings().first()
        try:
            res = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="ESCALATE",
                reviewer="test-p3-recapture", notes="re-review",
            )
            assert res["evidence_ref"]["linkage_status"] == "MISSING_SIDE_B"
        finally:
            await _cleanup_test_rows(session, [key], preserve={key: existing})

    @pytest.mark.asyncio
    async def test_evidence_merge_preserves_prior_provenance(self, session):
        """The ON CONFLICT merge is additive: re-capturing does not erase
        evidence recorded by an earlier pass."""
        svc = ReviewQueueService(session)
        key = ("TRIAGE", "test:merge:provenance")
        try:
            await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="REVIEW",
                reviewer="a", evidence={"pass": _FIRST_PASS, "reason": "first"},
            )
            res = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="REVIEW",
                reviewer="b", evidence={"pass": _SECOND_PASS},
            )
            assert res["evidence_ref"]["reason"] == "first", "prior evidence was lost"
            assert res["evidence_ref"]["pass"] == _SECOND_PASS
        finally:
            await _cleanup_test_rows(session, [key])


class TestUnresolvableSubjectRejected:
    """1.3 — a disposition is refused when its subject cannot be tied to a
    real Global Company, instead of being recorded with a dangling key."""

    @pytest.mark.asyncio
    async def test_p1_candidate_without_company_row_is_refused(self, session):
        svc = ReviewQueueService(session)
        fake = "00000000-0000-4000-8000-0000000000ff"
        # A P1 candidate must exist for this id, otherwise the earlier
        # candidate guard fires; force a candidate with no company row.
        await session.execute(
            text(
                "INSERT INTO md_review_candidates "
                "(id, global_entity_id, candidate_type, reason, source_ids, status) "
                "VALUES (CAST(:id AS uuid), CAST(:gid AS uuid), 'P1', :reason, "
                "        CAST(:src AS JSONB), 'pending')"
            ),
            {
                "id": "11111111-2222-4333-8444-0000000000ff",
                "gid": fake,
                "reason": _TEST_CANDIDATE_REASON,
                "src": json.dumps(["test:linkage"]),
            },
        )
        await session.commit()
        key = ("P1_CANDIDATE", fake)
        try:
            with pytest.raises(ValueError, match="not a real Global Company"):
                await svc.record_disposition(
                    queue_type=key[0], subject_key=key[1], disposition="REVIEW",
                    reviewer="test", notes="must be refused",
                )
            # Nothing may be written for a refused subject.
            count = await session.execute(
                text("SELECT COUNT(*) FROM md_review_queue_state "
                     "WHERE queue_type=:q AND subject_key=:k"),
                {"q": key[0], "k": key[1]},
            )
            assert count.scalar() == 0, "refused subject must leave no state row"
        finally:
            await session.execute(
                text("DELETE FROM md_review_candidates WHERE reason = :reason"),
                {"reason": _TEST_CANDIDATE_REASON},
            )
            await session.commit()
            await _cleanup_test_rows(session, [key])

    @pytest.mark.asyncio
    async def test_short_cr_malformed_subject_is_refused(self, session):
        svc = ReviewQueueService(session)
        with pytest.raises(ValueError, match="MA-XXXXXXX"):
            await svc.record_disposition(
                queue_type="SHORT_CR", subject_key="not-a-ma-id",
                disposition="CONFIRMED_ARTIFACT", reviewer="test", notes="bad key",
            )

    @pytest.mark.asyncio
    async def test_unknown_ma_is_refused_by_legacy_crosswalk_guard(self, session):
        """A syntactically valid MA that no mapping resolves must be refused."""
        svc = ReviewQueueService(session)
        with pytest.raises(ValueError, match="Global Company"):
            await svc.record_disposition(
                queue_type="SHORT_CR", subject_key="MA-9999999",
                disposition="CONFIRMED_ARTIFACT", reviewer="test", notes="unmapped MA",
            )

    @pytest.mark.asyncio
    async def test_p2_stratum_subject_is_not_company_gated(self, session):
        """The company guard is queue-specific: a P2 stratum is a sampling
        label, not a company, and must not be rejected for lacking one."""
        svc = ReviewQueueService(session)
        key = ("P2_SAMPLE", "P2:SALES_READY_WITH_REVIEW")
        existing = (
            await session.execute(
                text(
                    "SELECT status, disposition, reviewer, reviewed_at, notes, "
                    "global_company_id::text AS global_company_id, "
                    "global_company_id_b::text AS global_company_id_b, evidence_ref "
                    "FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"
                ),
                {"q": key[0], "k": key[1]},
            )
        ).mappings().first()
        try:
            res = await svc.record_disposition(
                queue_type=key[0], subject_key=key[1], disposition="ACCEPT_SAMPLE",
                reviewer="test-stratum", notes="0.00% observed error",
                evidence={"sample_n": 0, "stratum": "SALES_READY_WITH_REVIEW"},
            )
            assert res["global_company_id"] is None
            assert res["evidence_ref"]["stratum"] == "SALES_READY_WITH_REVIEW"
        finally:
            await _cleanup_test_rows(session, [key], preserve={key: existing})


def _valid_disposition(queue_type: str) -> str:
    if queue_type == "P3_PAIR":
        return "SEPARATE"
    if queue_type == "SHORT_CR":
        return "CONFIRMED_ARTIFACT"
    return "CONFIRM"


async def _cleanup_test_rows(session, keys, preserve=None) -> None:
    preserve = preserve or {}
    for qt, sk in keys:
        previous = preserve.get((qt, sk))
        if previous:
            # Restore EVERY column the capture path writes, otherwise the
            # evidence_ref merge / linkage write would permanently pollute
            # seeded rows.
            await session.execute(
                text(
                    "UPDATE md_review_queue_state SET status=:status, disposition=:disp, "
                    "reviewer=:reviewer, reviewed_at=:reviewed_at, notes=:notes, "
                    "global_company_id=CAST(:gid AS uuid), "
                    "global_company_id_b=CAST(:gid_b AS uuid), "
                    "evidence_ref=CAST(:ev AS JSONB) "
                    "WHERE queue_type=:q AND subject_key=:k"
                ),
                {
                    "q": qt,
                    "k": sk,
                    "status": previous["status"],
                    "disp": previous["disposition"],
                    "reviewer": previous["reviewer"],
                    "reviewed_at": previous["reviewed_at"],
                    "notes": previous["notes"],
                    "gid": previous["global_company_id"],
                    "gid_b": previous["global_company_id_b"],
                    "ev": json.dumps(previous["evidence_ref"] or {}),
                },
            )
        else:
            await session.execute(
                text("DELETE FROM md_review_queue_state WHERE queue_type=:q AND subject_key=:k"),
                {"q": qt, "k": sk},
            )
    await session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
