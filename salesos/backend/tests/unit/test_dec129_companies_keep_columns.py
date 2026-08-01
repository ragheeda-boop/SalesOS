"""DEC-129 / Phase 0 criterion 7.4: companies live columns must stay on ORM.

Prevents a silent re-STOP / accidental DROP of FTS and feature-store columns
that DEC-122 correctly refused to drop. Criterion 7.4 = KEEP + DEC recorded;
full alembic check remains 7.6.
"""

from __future__ import annotations

from app.modules.company.models import Company

# DEC-122 STOP set + sibling 0002 feature columns confirmed live in Docker DB.
# DEC-130e extends KEEP with do_not_contact + embedding_vector (criterion 7.6 Slice 5e).
_KEEP_COLUMNS = (
    "parent_company_id",
    "annual_revenue",
    "revenue_prev_year",
    "revenue_2yr_ago",
    "employee_count_prev_year",
    "linkedin_url",
    "country",
    "branch_count",
    "do_not_contact",
    "embedding_vector",
    "tsv",
    "search_vector",
)


def test_company_orm_keeps_live_feature_and_fts_columns():
    cols = set(Company.__table__.c.keys())
    missing = [name for name in _KEEP_COLUMNS if name not in cols]
    assert missing == [], (
        "DEC-129 / criterion 7.4: Company ORM missing live DB columns "
        f"(must KEEP, never DROP): {missing}"
    )


def test_company_search_vector_is_generated_persisted():
    """search_vector must remain GENERATED ALWAYS (FTS), not a writable dead col."""
    col = Company.__table__.c.search_vector
    assert col.computed is not None, "search_vector must use Computed (GENERATED ALWAYS)"
    assert col.computed.persisted is True
