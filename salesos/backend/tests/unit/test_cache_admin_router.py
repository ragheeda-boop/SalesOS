"""Cache admin router (/api/v1/cache/*) must call CacheService's real API,
and (DEC-159) must require the "admin" role, not just any authenticated user.

Mechanical finding: `set_cache` called `cache.set(..., ttl=...)` and
`flush_cache` called `cache.flush(pattern=...)`, but CacheService's actual
methods are `set(key, value, ttl_seconds=300)` and `delete_pattern(pattern)`
— neither `ttl` nor `flush` exist on the class. Both endpoints raised an
unhandled TypeError/AttributeError on every call.

DEC-159: this router previously required only `verify_token` (any
authenticated user, any role, any tenant) — a raw caller-supplied-key
get/set/delete plus a wildcard `flush(pattern="*")` is a wider blast radius
than most per-tenant endpoints, so it now requires the "admin" role via
`require_role_dep("admin")`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import get_current_user_role
from app.modules.cache.router import router as cache_router
from sdk.cache import CacheService


class WorkingRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self._store[key] = value

    async def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)

    async def exists(self, key: str):
        return 1 if key in self._store else 0

    async def flushall(self):
        self._store.clear()

    async def scan(self, cursor: int = 0, match: str = "*"):
        import fnmatch

        keys = [k for k in self._store if fnmatch.fnmatch(k, match)]
        return 0, keys

    async def ping(self):
        return True


class _TestCacheService(CacheService):
    """Adds the health() override app.cache.CacheService has in production."""

    async def health(self) -> bool:
        return bool(await self._redis.ping())


def _make_app(role: str = "admin") -> FastAPI:
    app = FastAPI()
    app.include_router(cache_router)
    app.dependency_overrides[get_current_user_role] = lambda: role
    app.state.cache = _TestCacheService(WorkingRedis())
    return app


def test_set_then_get_roundtrip():
    with TestClient(_make_app()) as client:
        resp = client.post(
            "/api/v1/cache/set", json={"key": "k1", "value": "v1", "ttl": 60}
        )
        assert resp.status_code == 200, resp.text
        resp = client.get("/api/v1/cache/k1")
        assert resp.status_code == 200
        assert resp.json() == {"key": "k1", "value": "v1"}


def test_delete_removes_key():
    with TestClient(_make_app()) as client:
        client.post("/api/v1/cache/set", json={"key": "k2", "value": "v2", "ttl": 60})
        resp = client.delete("/api/v1/cache/k2")
        assert resp.status_code == 200, resp.text
        resp = client.get("/api/v1/cache/k2")
        assert resp.status_code == 404


def test_flush_clears_matching_keys():
    with TestClient(_make_app()) as client:
        client.post("/api/v1/cache/set", json={"key": "pfx:a", "value": "1", "ttl": 60})
        client.post("/api/v1/cache/set", json={"key": "pfx:b", "value": "2", "ttl": 60})
        resp = client.post("/api/v1/cache/flush", json={"pattern": "pfx:*"})
        assert resp.status_code == 200, resp.text
        assert client.get("/api/v1/cache/pfx:a").status_code == 404
        assert client.get("/api/v1/cache/pfx:b").status_code == 404


def test_health_reports_connected():
    with TestClient(_make_app()) as client:
        resp = client.get("/api/v1/cache/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "connected"}


def test_non_admin_role_is_rejected_on_every_endpoint():
    with TestClient(_make_app(role="user")) as client:
        assert client.get("/api/v1/cache/health").status_code == 403
        assert client.get("/api/v1/cache/k1").status_code == 403
        assert (
            client.post(
                "/api/v1/cache/set", json={"key": "k1", "value": "v1", "ttl": 60}
            ).status_code
            == 403
        )
        assert client.delete("/api/v1/cache/k1").status_code == 403
        assert (
            client.post("/api/v1/cache/flush", json={"pattern": "*"}).status_code == 403
        )


def test_manager_role_is_also_rejected_admin_only():
    with TestClient(_make_app(role="manager")) as client:
        assert client.get("/api/v1/cache/health").status_code == 403
