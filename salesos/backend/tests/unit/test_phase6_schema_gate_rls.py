"""Safety contract for the Phase 6 test-database schema gate."""

from scripts.phase6_schema_gate import RLS_TABLES, _rl_sql, _source_immutability_sql


def test_tenant_source_tables_are_in_rls_table_list():
    assert "md_source_files" in RLS_TABLES
    assert "md_source_rows" in RLS_TABLES


def test_source_values_rls_is_derived_from_tenant_scoped_source_row():
    sql = "\n".join(_rl_sql())
    assert 'ALTER TABLE "md_source_values" ENABLE ROW LEVEL SECURITY' in sql
    assert 'ALTER TABLE "md_source_values" FORCE ROW LEVEL SECURITY' in sql
    assert "sr.id = md_source_values.source_row_id" in sql
    assert "sr.tenant_id::text = current_setting('app.tenant_id', true)" in sql


def test_global_master_tables_are_not_added_to_tenant_rls_list():
    assert not {
        "md_global_companies",
        "md_global_people",
        "md_legacy_id_mappings",
    }.intersection(RLS_TABLES)


def test_source_immutability_guards_freeze_raw_values_and_delete():
    sql = "\n".join(_source_immutability_sql())
    assert "source evidence rows are append-only" in sql
    assert "NEW.raw_payload" in sql
    assert "NEW.original_value" in sql
    assert "trg_md_source_files_immutable" in sql
    assert "trg_md_source_rows_immutable" in sql
    assert "trg_md_source_values_immutable" in sql
