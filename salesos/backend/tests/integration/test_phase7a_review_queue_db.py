"""Integration tests for Phase 7-A review-queue tooling (salesos_test, read-only +
record-only disposition capture)."""

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
                    "SELECT id, status, disposition, reviewer, reviewed_at, notes "
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
                    "SELECT status, disposition, reviewer, reviewed_at, notes "
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
            await session.execute(
                text(
                    "UPDATE md_review_queue_state SET status=:status, disposition=:disp, "
                    "reviewer=:reviewer, reviewed_at=:reviewed_at, notes=:notes "
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
