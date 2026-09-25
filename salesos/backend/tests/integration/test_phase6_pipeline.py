"""Integration tests for Phase 6 pipeline (salesos_test, dry-run mode)."""

from uuid import uuid4

import asyncpg
import pytest

from app.modules.master_data.phase6.pipeline import Phase6Pipeline

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"
SAMPLE_SIZE = 100
STREAMED_BATCH_COUNT = 2


@pytest.fixture
async def db_conn():
    """Async DB connection fixture for salesos_test."""
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    db = await conn.fetchval("SELECT current_database()")
    assert db == "salesos_test", f"Must run on salesos_test, got {db}"
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
def pipeline(db_conn):
    """Phase 6 pipeline in dry-run mode."""
    return Phase6Pipeline(db_conn, dry_run=True)


class TestPhase6Pipeline:
    """Test the full Phase 6 pipeline execution."""

    def test_staged_counts_accumulate_across_streamed_batches(self):
        """The streamed dry-run summary must count every flushed batch."""
        pipeline = Phase6Pipeline(None, dry_run=True)
        for _ in range(STREAMED_BATCH_COUNT):
            pipeline._identity_rows.append(
                (str(uuid4()), "VALID", "READY", "P1", "SAFE")
            )
            pipeline._flush_dry_run_batch()

        assert (
            pipeline._staged_counts["identity_classifications"]
            == STREAMED_BATCH_COUNT
        )
        assert pipeline.change_count == STREAMED_BATCH_COUNT

    def test_phase6_rejects_synthetic_company_keys(self):
        """Derived rows must never invent a Global Company UUID."""
        pipeline = Phase6Pipeline(None, dry_run=True)
        with pytest.raises(ValueError, match="authoritative Global Company UUID"):
            pipeline._to_uuid("gc-MA-0000001")

    @pytest.mark.asyncio
    async def test_bounded_dry_run_processes_a_sample_without_database_writes(self, pipeline):
        """A deterministic sample run should stay dry-run and identify its limit."""
        tables = [
            "md_identity_classifications",
            "md_review_candidates",
            "md_industry_normalization",
            "md_quality_score_history",
            "md_sales_readiness_history",
        ]
        before = {
            table: await pipeline.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            for table in tables
        }

        result = await pipeline.run(max_accounts=SAMPLE_SIZE)

        after = {
            table: await pipeline.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            for table in tables
        }
        assert result["dry_run"] is True
        assert result["summary"]["sampled_run"] is True
        assert result["summary"]["sample_limit"] == SAMPLE_SIZE
        assert result["summary"]["master_accounts_loaded"] == SAMPLE_SIZE
        assert result["staged"]["identity_classifications"] == SAMPLE_SIZE
        assert before == after
        assert not any(result["safety"].values())

    @pytest.mark.asyncio
    async def test_bounded_run_refuses_write_mode(self):
        """A sampled run must never be used for a partial database write."""
        pipeline = Phase6Pipeline(None, dry_run=False)
        with pytest.raises(ValueError, match="only in dry-run mode"):
            await pipeline.run(max_accounts=SAMPLE_SIZE)

    @pytest.mark.asyncio
    async def test_dry_run_completes(self, pipeline):
        """Pipeline runs to completion without errors in dry-run mode."""
        result = await pipeline.run()
        assert result["dry_run"] is True
        assert result["version"] == "OPTION_C_1"

    @pytest.mark.asyncio
    async def test_all_master_accounts_processed(self, pipeline):
        """All 296,746 master accounts are processed."""
        result = await pipeline.run()
        assert result["summary"]["master_accounts_loaded"] == 296_746
        assert result["staged"]["identity_classifications"] == 296_746

    @pytest.mark.asyncio
    async def test_identity_states_distribution(self, pipeline):
        """Identity state distribution matches expected ranges."""
        result = await pipeline.run()
        states = result["summary"]["identity_states"]

        # Total must close exactly to 296,746.
        assert sum(states.values()) == 296_746
        # NO_VERIFIABLE_IDENTITY should be largest (~242k per DI reconciliation)
        assert states.get("NO_VERIFIABLE_IDENTITY", 0) > 230_000
        # DETERMINISTIC_SINGLE_SOURCE ~45-50k
        assert states.get("DETERMINISTIC_SINGLE_SOURCE", 0) > 40_000
        # GOVERNMENT_ANCHORED ~3-3.5k (valid CR + MATCHED confidence)
        assert states.get("GOVERNMENT_ANCHORED", 0) > 3_000
        # STRONG_MULTI_SOURCE — D1 fix — must be NON-ZERO (was 0 before fix).
        assert states.get("STRONG_MULTI_SOURCE", 0) > 2_000

    @pytest.mark.asyncio
    async def test_d1_strong_multi_source_produced(self, pipeline):
        """D1 fix: STRONG_MULTI_SOURCE must be non-zero (was 0)."""
        result = await pipeline.run()
        assert result["summary"]["identity_states"].get("STRONG_MULTI_SOURCE", 0) > 0

    @pytest.mark.asyncio
    async def test_d2_identity_classification_references_real_company(self, pipeline):
        """D2 fix: every identity classification global_entity_id is a real company."""
        result = await pipeline.run()
        # In dry-run the rows are staged in memory; verify via a real-company
        # sanity check on the sample.
        assert pipeline.ma_to_company  # populated
        # Verify all staged identity rows use real company IDs (no synthetic).
        assert pipeline._identity_sample_rows
        for row in pipeline._identity_sample_rows:
            cid = row[0]
            exists = await pipeline.conn.fetchval(
                "SELECT COUNT(*) FROM md_global_companies WHERE id = $1", cid)
            assert exists == 1, f"identity row references non-company id {cid}"

    @pytest.mark.asyncio
    async def test_cr_class_distribution(self, pipeline):
        """CR class distribution matches Phase 5 reconciliation."""
        result = await pipeline.run()
        classes = result["summary"]["cr_classes"]

        # Phase 5 verified: SAFE 15,419 + SUSPICIOUS_SHORT 3,924 + SUSPICIOUS_MULTI 36
        assert classes.get("SAFE", 0) == 15_419
        assert classes.get("SUSPICIOUS_SHORT", 0) == 3_924
        assert classes.get("SUSPICIOUS_MULTI", 0) == 36
        assert classes.get("AMBIGUOUS", 0) == 277_367

    @pytest.mark.asyncio
    async def test_review_priorities(self, pipeline):
        """Review priority distribution."""
        result = await pipeline.run()
        priorities = result["summary"]["priorities"]

        # P4 (NO_VERIFIABLE_IDENTITY) should be largest
        assert priorities.get("P4", 0) > 230_000
        # P2 (DETERMINISTIC_SINGLE_SOURCE + WEAK_IDENTITY)
        assert priorities.get("P2", 0) > 40_000
        # P1 (GOVERNMENT_ANCHORED + STRONG_MULTI_SOURCE + some REVIEW)
        assert priorities.get("P1", 0) > 3_000
        # P3 (fuzzy candidates)
        assert priorities.get("P3", 0) >= 0

    @pytest.mark.asyncio
    async def test_industry_normalizations(self, pipeline):
        """Industry normalizations staged for accounts with industry data."""
        result = await pipeline.run()
        assert result["staged"]["industry_normalizations"] > 290_000

    @pytest.mark.asyncio
    async def test_quality_history_entries(self, pipeline):
        """Quality score history entries for all accounts."""
        result = await pipeline.run()
        assert result["staged"]["quality_history"] == 296_746

    @pytest.mark.asyncio
    async def test_sales_readiness_history_entries(self, pipeline):
        """Sales readiness history entries for all accounts."""
        result = await pipeline.run()
        assert result["staged"]["sales_readiness_history"] == 296_746

    @pytest.mark.asyncio
    async def test_contact_relationships(self, pipeline):
        """Contact relationships staged from muhide_contacts."""
        result = await pipeline.run()
        assert result["summary"]["contact_relationships_staged"] == 1_102

    @pytest.mark.asyncio
    async def test_all_safety_counters_zero(self, pipeline):
        """All safety counters MUST be zero in dry-run."""
        result = await pipeline.run()
        safety = result.get("safety", {})

        # Core safety counters
        assert safety.get("source_rows_modified", 0) == 0
        assert safety.get("raw_payload_modified", 0) == 0
        assert safety.get("global_ids_changed", 0) == 0
        assert safety.get("existing_entities_deleted", 0) == 0
        assert safety.get("fuzzy_auto_merges", 0) == 0
        assert safety.get("government_id_vetoes_bypassed", 0) == 0
        assert safety.get("apollo_calls", 0) == 0
        assert safety.get("external_api_calls", 0) == 0
        assert safety.get("production_writes", 0) == 0

    @pytest.mark.asyncio
    async def test_idempotency_same_results(self, pipeline):
        """Running pipeline twice produces identical staged counts."""
        result1 = await pipeline.run()
        result2 = await pipeline.run()

        assert result1["staged"] == result2["staged"]
        assert result1["summary"]["master_accounts_loaded"] == result2["summary"]["master_accounts_loaded"]
        assert result1["summary"]["identity_states"] == result2["summary"]["identity_states"]

    @pytest.mark.asyncio
    async def test_change_log_not_empty(self, pipeline):
        """Dry run produces change log entries."""
        result = await pipeline.run()
        assert result["change_count"] > 0
        # Should have at least identity_classifications + quality + readiness + industry + candidates + relationships
        expected_min = 296_746 * 4 + 50_000 + 1_102
        assert result["change_count"] >= expected_min


class TestPhase6PipelineSchema:
    """Verify Phase 6 tables exist and have correct schema."""

    @pytest.mark.asyncio
    async def test_phase6_tables_exist(self, db_conn):
        """All 7 Phase 6 tables exist in salesos_test."""
        tables = await db_conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
        )
        table_names = {r["tablename"] for r in tables}

        phase6_tables = {
            "md_identity_classifications",
            "md_review_candidates",
            "md_p0_dispositions",
            "md_industry_normalization",
            "md_contact_relationships",
            "md_quality_score_history",
            "md_sales_readiness_history",
        }
        assert phase6_tables.issubset(table_names)

    @pytest.mark.asyncio
    async def test_identity_classifications_columns(self, db_conn):
        """md_identity_classifications has required columns."""
        cols = await db_conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name='md_identity_classifications'"
        )
        col_names = {r["column_name"] for r in cols}
        required = {
            "id", "global_entity_id", "classification_version", "identity_state",
            "sales_readiness", "review_priority", "cr_class", "has_cr",
            "has_vat", "has_unified", "has_real_domain", "independent_source_count",
            "source_count", "conflicts", "signals", "source_ids", "computed_at"
        }
        assert required.issubset(col_names)

    @pytest.mark.asyncio
    async def test_review_candidates_unique_constraint(self, db_conn):
        """md_review_candidates has unique constraint on (global_entity_id, candidate_type, reason)."""
        constraints = await db_conn.fetch(
            """SELECT conname FROM pg_constraint WHERE conrelid = 'md_review_candidates'::regclass
               AND contype = 'u'"""
        )
        con_names = {r["conname"] for r in constraints}
        assert any("uq_md_review_candidate" in n for n in con_names)

    @pytest.mark.asyncio
    async def test_industry_normalization_unique_constraint(self, db_conn):
        """md_industry_normalization has unique constraint on (global_entity_id, raw_industry, normalization_method)."""
        constraints = await db_conn.fetch(
            """SELECT conname FROM pg_constraint WHERE conrelid = 'md_industry_normalization'::regclass
               AND contype = 'u'"""
        )
        con_names = {r["conname"] for r in constraints}
        assert any("uq_md_industry_norm" in n for n in con_names)

    @pytest.mark.asyncio
    async def test_contact_relationships_unique_constraint(self, db_conn):
        """md_contact_relationships has unique constraint on (person_global_id, company_global_id, linking_basis)."""
        constraints = await db_conn.fetch(
            """SELECT conname FROM pg_constraint WHERE conrelid = 'md_contact_relationships'::regclass
               AND contype = 'u'"""
        )
        con_names = {r["conname"] for r in constraints}
        assert any("uq_md_contact_rel" in n for n in con_names)

    @pytest.mark.asyncio
    async def test_quality_history_unique_constraint(self, db_conn):
        """md_quality_score_history has unique constraint on (global_entity_id, calc_version)."""
        constraints = await db_conn.fetch(
            """SELECT conname FROM pg_constraint WHERE conrelid = 'md_quality_score_history'::regclass
               AND contype = 'u'"""
        )
        con_names = {r["conname"] for r in constraints}
        assert any("uq_md_quality_hist" in n for n in con_names)

    @pytest.mark.asyncio
    async def test_sales_readiness_unique_constraint(self, db_conn):
        """md_sales_readiness_history has unique constraint on (global_entity_id, calc_version)."""
        constraints = await db_conn.fetch(
            """SELECT conname FROM pg_constraint WHERE conrelid = 'md_sales_readiness_history'::regclass
               AND contype = 'u'"""
        )
        con_names = {r["conname"] for r in constraints}
        assert any("uq_md_sales_readiness" in n for n in con_names)

    @pytest.mark.asyncio
    async def test_no_rls_on_phase6_global_tables(self, db_conn):
        """Phase 6 tables are GLOBAL (no RLS) per DI contract."""
        for table in [
            "md_identity_classifications", "md_review_candidates",
            "md_p0_dispositions", "md_industry_normalization",
            "md_contact_relationships", "md_quality_score_history",
            "md_sales_readiness_history",
        ]:
            rls = await db_conn.fetchval(
                f"SELECT relrowsecurity FROM pg_class WHERE relname = '{table}'"
            )
            assert rls is False, f"Table {table} should not have RLS enabled"


class TestPhase6D2EntityLinkage:
    """D2 fix: derived records must reference REAL md_global_companies IDs."""

    @pytest.mark.asyncio
    async def test_identity_classifications_link_to_real_companies(self, db_conn):
        """Every identity classification global_entity_id exists in md_global_companies."""
        total = await db_conn.fetchval("SELECT COUNT(*) FROM md_identity_classifications")
        if total == 0:
            pytest.skip("identity classifications not yet persisted")
        orphan = await db_conn.fetchval(
            """SELECT COUNT(*) FROM md_identity_classifications ic
               WHERE NOT EXISTS (SELECT 1 FROM md_global_companies gc WHERE gc.id = ic.global_entity_id)"""
        )
        assert orphan == 0, f"{orphan} orphan identity classifications"

    @pytest.mark.asyncio
    async def test_review_candidates_link_to_real_companies(self, db_conn):
        """Every review candidate global_entity_id exists in md_global_companies."""
        total = await db_conn.fetchval("SELECT COUNT(*) FROM md_review_candidates")
        if total == 0:
            pytest.skip("review candidates not yet persisted")
        orphan = await db_conn.fetchval(
            """SELECT COUNT(*) FROM md_review_candidates rc
               WHERE NOT EXISTS (SELECT 1 FROM md_global_companies gc WHERE gc.id = rc.global_entity_id)"""
        )
        assert orphan == 0, f"{orphan} orphan review candidates"

    @pytest.mark.asyncio
    async def test_no_synthetic_company_ids(self, db_conn):
        """No derived record carries a synthetic company UUID (phase6: namespace)."""
        for table in ["md_identity_classifications", "md_review_candidates",
                      "md_industry_normalization", "md_quality_score_history",
                      "md_sales_readiness_history"]:
            total = await db_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            if total == 0:
                continue
            orphan = await db_conn.fetchval(
                f"""SELECT COUNT(*) FROM {table} t
                    WHERE NOT EXISTS (SELECT 1 FROM md_global_companies gc WHERE gc.id = t.global_entity_id)"""
            )
            assert orphan == 0, f"{table}: {orphan} non-company global_entity_id refs"

    @pytest.mark.asyncio
    async def test_industry_normalization_link_to_real_companies(self, db_conn):
        total = await db_conn.fetchval("SELECT COUNT(*) FROM md_industry_normalization")
        if total == 0:
            pytest.skip("industry normalization not yet persisted")
        orphan = await db_conn.fetchval(
            """SELECT COUNT(*) FROM md_industry_normalization tn
               WHERE NOT EXISTS (SELECT 1 FROM md_global_companies gc WHERE gc.id = tn.global_entity_id)"""
        )
        assert orphan == 0, f"{orphan} orphan industry normalizations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
