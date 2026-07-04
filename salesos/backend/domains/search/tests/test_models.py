"""Tests for SearchQuery and SearchResult contracts."""

from domains.search.contracts.models import SearchFacet, SearchQuery, SearchResult, SearchSort


def test_search_query_defaults():
    q = SearchQuery()
    assert q.query == ""
    assert q.filters == {}
    assert q.sort is None
    assert q.page == 1
    assert q.page_size == 20
    assert q.tenant_id == ""


def test_search_query_with_values():
    q = SearchQuery(
        query="شركة اختبار",
        filters={"status": "active", "city": {"contains": "الرياض"}},
        sort=SearchSort(field="created_at", direction="desc"),
        page=2,
        page_size=10,
        tenant_id="tenant-123",
    )
    assert q.query == "شركة اختبار"
    assert q.filters["status"] == "active"
    assert q.sort.field == "created_at"
    assert q.page == 2
    assert q.page_size == 10
    assert q.tenant_id == "tenant-123"


def test_search_result_defaults():
    r = SearchResult()
    assert r.items == []
    assert r.total == 0
    assert r.page == 1
    assert r.page_size == 20
    assert r.facets == []
    assert r.duration_ms == 0.0
    assert r.query == ""
    assert r.strategy == "postgres"
    assert r.ranking_version == "1.0"
    assert r.next_cursor is None


def test_search_result_with_items():
    items = [{"id": 1, "name": "Test"}]
    facets = [SearchFacet(field="status", values={"active": 5, "inactive": 2})]
    r = SearchResult(
        items=items,
        total=1,
        page=1,
        page_size=20,
        facets=facets,
        filters={"status": "active"},
        duration_ms=15.5,
        query="test",
        strategy="postgres",
        ranking_version="1.0",
    )
    assert r.items == items
    assert r.total == 1
    assert len(r.facets) == 1
    assert r.facets[0].values["active"] == 5
    assert r.duration_ms == 15.5


def test_search_sort():
    s = SearchSort(field="name_ar", direction="asc")
    assert s.field == "name_ar"
    assert s.direction == "asc"


def test_search_facet():
    f = SearchFacet(field="city", values={"الرياض": 10, "جدة": 5})
    assert f.field == "city"
    assert f.values["الرياض"] == 10
