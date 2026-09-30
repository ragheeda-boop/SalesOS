"""RateLimitMiddleware must dispatch the downstream app exactly once.

Regression: the downstream call used to sit inside the Redis try/except, so an
app exception was treated as a Redis failure and the request was replayed
against an already-drained body (register hung).
"""

from __future__ import annotations

import pytest

from app.common import middleware as mw
from app.common.middleware import RateLimitMiddleware


class _Redis:
    def __init__(self, fail: bool) -> None:
        self.fail = fail

    async def incr(self, key: str) -> int:
        if self.fail:
            raise ConnectionError("redis down")
        return 1

    async def expire(self, key: str, window: int) -> None:
        return None


def _scope(path: str = "/other") -> dict:
    return {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("10.0.0.1", 1234),
        "server": ("test", 80),
        "scheme": "http",
    }


async def _receive() -> dict:
    return {"type": "http.request", "body": b"", "more_body": False}


@pytest.fixture(autouse=True)
def _not_testing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SALESOS_TESTING", raising=False)
    monkeypatch.setattr(mw.settings, "rate_limit_default", 2)


async def test_app_exception_propagates_without_replay() -> None:
    calls = 0

    async def app(scope, receive, send):
        nonlocal calls
        calls += 1
        raise RuntimeError("handler failed")

    limiter = RateLimitMiddleware(app, redis_client=_Redis(fail=False))
    with pytest.raises(RuntimeError, match="handler failed"):
        await limiter(_scope(), _receive, lambda m: None)
    assert calls == 1


async def test_redis_down_falls_back_to_memory_and_still_limits() -> None:
    calls = 0
    sent: list[dict] = []

    async def app(scope, receive, send):
        nonlocal calls
        calls += 1

    async def send(message: dict) -> None:
        sent.append(message)

    limiter = RateLimitMiddleware(app, redis_client=_Redis(fail=True))
    for _ in range(3):
        await limiter(_scope(), _receive, send)

    assert calls == 2
    statuses = [m["status"] for m in sent if m["type"] == "http.response.start"]
    assert statuses == [429]
