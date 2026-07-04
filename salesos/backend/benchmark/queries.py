"""Benchmark query definitions — each query is a named, measurable scenario.

Each scenario is a dict with:
    name: str
    description: str
    category: "exact" | "partial" | "filter" | "sort" | "pagination" | "count"
    sql: str (parameterized with :placeholders)
    params: dict of parameter values
    explain: bool (run EXPLAIN ANALYZE if True)
"""

from __future__ import annotations

import math

QUERIES: list[dict] = []

TENANT_ID_PLACEHOLDER = "11111111-1111-1111-1111-111111111111"

# PostgreSQL requires ::uuid for UUID columns; SQLite/TEXT don't.
# The benchmark normalizes this by removing ::uuid at runtime.
PG_UUID_CAST = "::uuid"

# ─────────────────────────────────────────────
# 1. EXACT SEARCH
# ─────────────────────────────────────────────

QUERIES.append({
    "name": "exact_search_by_cr",
    "description": "Exact match on cr_number (unique, indexed)",
    "category": "exact",
    "sql": "SELECT * FROM companies WHERE cr_number = :cr_number AND tenant_id = :tenant_id::uuid",
    "params": {"cr_number": "1012345678", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "exact_search_by_name_ar",
    "description": "Exact match on name_ar (indexed)",
    "category": "exact",
    "sql": "SELECT * FROM companies WHERE name_ar = :name_ar AND tenant_id = :tenant_id::uuid",
    "params": {"name_ar": "شركة الأمل للتجارة", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

# ─────────────────────────────────────────────
# 2. PARTIAL SEARCH
# ─────────────────────────────────────────────

QUERIES.append({
    "name": "partial_search_name_ar",
    "description": "ILIKE on name_ar (prefix match)",
    "category": "partial",
    "sql": "SELECT * FROM companies WHERE name_ar ILIKE :pattern AND tenant_id = :tenant_id::uuid",
    "params": {"pattern": "شركة%", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "partial_search_name_ar_middle",
    "description": "ILIKE on name_ar (middle match — worst case)",
    "category": "partial",
    "sql": "SELECT * FROM companies WHERE name_ar ILIKE :pattern AND tenant_id = :tenant_id::uuid",
    "params": {"pattern": "%تجارة%", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "partial_search_cr_number",
    "description": "ILIKE on cr_number",
    "category": "partial",
    "sql": "SELECT * FROM companies WHERE cr_number ILIKE :pattern AND tenant_id = :tenant_id::uuid",
    "params": {"pattern": "10%", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "partial_search_city",
    "description": "ILIKE on city",
    "category": "partial",
    "sql": "SELECT * FROM companies WHERE city ILIKE :pattern AND tenant_id = :tenant_id::uuid",
    "params": {"pattern": "الرياض%", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

# ─────────────────────────────────────────────
# 3. MULTI-FILTER
# ─────────────────────────────────────────────

QUERIES.append({
    "name": "multi_filter_status_city",
    "description": "Status (exact) + City (prefix)",
    "category": "filter",
    "sql": (
        "SELECT * FROM companies "
        "WHERE status = :status AND city ILIKE :city "
        "AND tenant_id = :tenant_id::uuid"
    ),
    "params": {"status": "active", "city": "الرياض%", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "multi_filter_status_region_activity",
    "description": "Status + Region + Activity (3 filters)",
    "category": "filter",
    "sql": (
        "SELECT * FROM companies "
        "WHERE status = :status AND region = :region "
        "AND activity_description ILIKE :activity "
        "AND tenant_id = :tenant_id::uuid"
    ),
    "params": {
        "status": "active",
        "region": "الرياض",
        "activity": "%تجارة%",
        "tenant_id": TENANT_ID_PLACEHOLDER,
    },
    "explain": True,
})

QUERIES.append({
    "name": "multi_filter_legal_form_status",
    "description": "Legal form + Status + City",
    "category": "filter",
    "sql": (
        "SELECT * FROM companies "
        "WHERE legal_form = :legal_form AND status = :status "
        "AND city = :city AND tenant_id = :tenant_id::uuid"
    ),
    "params": {
        "legal_form": "شركة ذات مسؤولية محدودة",
        "status": "active",
        "city": "جدة",
        "tenant_id": TENANT_ID_PLACEHOLDER,
    },
    "explain": True,
})

# ─────────────────────────────────────────────
# 4. SORTING
# ─────────────────────────────────────────────

for direction in ["ASC", "DESC"]:
    QUERIES.append({
        "name": f"sort_by_created_at_{direction.lower()}",
        "description": f"Sort by created_at {direction}",
        "category": "sort",
        "sql": (
            "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
            f"ORDER BY created_at {direction} NULLS LAST LIMIT 20"
        ),
        "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
        "explain": True,
    })

    QUERIES.append({
        "name": f"sort_by_name_ar_{direction.lower()}",
        "description": f"Sort by name_ar {direction}",
        "category": "sort",
        "sql": (
            "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
            f"ORDER BY name_ar {direction} NULLS LAST LIMIT 20"
        ),
        "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
        "explain": True,
    })

    QUERIES.append({
        "name": f"sort_by_confidence_score_{direction.lower()}",
        "description": f"Sort by confidence_score {direction}",
        "category": "sort",
        "sql": (
            "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
            f"ORDER BY confidence_score {direction} NULLS LAST LIMIT 20"
        ),
        "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
        "explain": True,
    })

# ─────────────────────────────────────────────
# 5. PAGINATION
# ─────────────────────────────────────────────

QUERIES.append({
    "name": "pagination_page_1",
    "description": "LIMIT 20 OFFSET 0",
    "category": "pagination",
    "sql": (
        "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
        "ORDER BY created_at DESC LIMIT 20 OFFSET 0"
    ),
    "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "pagination_page_mid",
    "description": "LIMIT 20 OFFSET 500 (deep pagination)",
    "category": "pagination",
    "sql": (
        "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
        "ORDER BY created_at DESC LIMIT 20 OFFSET 500"
    ),
    "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "pagination_page_deep",
    "description": "LIMIT 20 OFFSET 5000 (very deep pagination)",
    "category": "pagination",
    "sql": (
        "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
        "ORDER BY created_at DESC LIMIT 20 OFFSET 5000"
    ),
    "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "pagination_page_large_size",
    "description": "LIMIT 100 OFFSET 0 (large page size)",
    "category": "pagination",
    "sql": (
        "SELECT * FROM companies WHERE tenant_id = :tenant_id::uuid "
        "ORDER BY created_at DESC LIMIT 100 OFFSET 0"
    ),
    "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

# ─────────────────────────────────────────────
# 6. COUNT QUERIES
# ─────────────────────────────────────────────

QUERIES.append({
    "name": "count_all",
    "description": "COUNT(*) with tenant filter",
    "category": "count",
    "sql": "SELECT COUNT(*) FROM companies WHERE tenant_id = :tenant_id::uuid",
    "params": {"tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})

QUERIES.append({
    "name": "count_with_filter",
    "description": "COUNT(*) with status + city filter",
    "category": "count",
    "sql": (
        "SELECT COUNT(*) FROM companies "
        "WHERE tenant_id = :tenant_id::uuid AND status = :status AND city = :city"
    ),
    "params": {"status": "active", "city": "الرياض", "tenant_id": TENANT_ID_PLACEHOLDER},
    "explain": True,
})


def get_queries_for_dataset(dataset_size: int) -> list[dict]:
    """Return queries with realistic params for the given dataset size."""
    qs = [dict(q) for q in QUERIES]  # deep copy

    offset_mid = max(1, dataset_size // 5)
    offset_deep = max(1, dataset_size // 2)

    for q in qs:
        if q["name"] == "pagination_page_mid":
            q["sql"] = q["sql"].replace("OFFSET 500", f"OFFSET {offset_mid}")
        if q["name"] == "pagination_page_deep":
            q["sql"] = q["sql"].replace("OFFSET 5000", f"OFFSET {offset_deep}")

    return qs
