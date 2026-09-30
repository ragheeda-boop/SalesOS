"""GET /reviews/pending and /reviews/kpis must not be shadowed by /reviews/{review_id}."""

from starlette.routing import Match

from app.routers.commercial import router


def _first_get_match(path: str) -> str:
    scope = {"type": "http", "method": "GET", "path": path, "root_path": ""}
    for route in router.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return route.endpoint.__name__
    raise AssertionError(f"no GET route matches {path}")


def test_pending_route_is_not_shadowed():
    assert _first_get_match("/reviews/pending") == "list_pending_reviews"


def test_kpis_route_is_not_shadowed():
    assert _first_get_match("/reviews/kpis") == "review_kpis"


def test_review_by_id_still_resolves():
    assert _first_get_match("/reviews/abc-123") == "get_review"
