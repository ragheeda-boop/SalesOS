"""runtime/odoo/__init__.py had zero prior test coverage. Two independent,
stacked bugs on the only live path (odoo_sync_all, scheduled in
app/celery_schedule.py):

Bug 1: OdooClientProtocol declares search_read/count/read as `async def`,
matching every OdooSyncService call site's `await self._client.search_read(...)`.
OdooJsonRpcClient's implementations were plain `def` (blocking urllib) --
`await <list>` raises `TypeError: object list can't be used in 'await'
expression` on the very first real sync attempt. The class's own docstring
already documented the intended fix ("wrap in asyncio.to_thread for async")
but it was never actually wired.

Bug 2, masking bug 1 entirely for the only real caller: `_run_odoo_sync()`
was a plain `def` that called `asyncio.run(_sync())` internally, but its
sole caller (`odoo_sync_all`'s own `_run()` coroutine) is already running
inside an event loop via the outer `asyncio.run(_run())` -- calling
`asyncio.run()` from within a running loop raises
`RuntimeError: asyncio.run() cannot be called from a running event loop`,
confirmed live and reproduced in isolation before attributing it to this
file. This fired before execution ever reached bug 1's code path.

Fixed: `_search_read_sync`/`_count_sync`/`_read_sync` keep the original
blocking urllib implementation; new `async def search_read/count/read`
wrappers delegate via `asyncio.to_thread`. `_run_odoo_sync` is now a real
`async def`, awaited directly by its sole caller instead of wrapping itself
in a second `asyncio.run()`.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from runtime.odoo import OdooConfig, OdooJsonRpcClient


def _config() -> OdooConfig:
    return OdooConfig(url="https://odoo.example.com", database="db", username="u", api_key="k")


@pytest.mark.asyncio
async def test_search_read_is_awaitable_and_returns_the_blocking_result():
    client = OdooJsonRpcClient(_config())
    client._uid = 1  # skip the internal authenticate() round-trip
    with patch.object(client, "_call", return_value=[{"id": 1, "name": "Acme"}]) as mock_call:
        result = await client.search_read("res.partner", [], fields=["name"])
    assert result == [{"id": 1, "name": "Acme"}]
    assert mock_call.called


@pytest.mark.asyncio
async def test_count_is_awaitable():
    client = OdooJsonRpcClient(_config())
    client._uid = 1
    with patch.object(client, "_call", return_value=7):
        result = await client.count("res.partner", [])
    assert result == 7


@pytest.mark.asyncio
async def test_read_is_awaitable():
    client = OdooJsonRpcClient(_config())
    client._uid = 1
    with patch.object(client, "_call", return_value=[{"id": 1}]):
        result = await client.read("res.partner", [1])
    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_run_odoo_sync_does_not_raise_nested_asyncio_run_from_a_running_loop():
    """Reproduces odoo_sync_all's real call shape: _run_odoo_sync() awaited
    from inside a coroutine that is itself already running under
    asyncio.run() (this test function, under pytest-asyncio's loop)."""
    from runtime.odoo import OdooSyncService, _run_odoo_sync

    async def _fake_run_full_sync(self, tenant_id, limit):
        return {"tenant_id": tenant_id, "limit": limit, "ok": True}

    with (
        patch.object(OdooSyncService, "run_full_sync", _fake_run_full_sync),
        patch("runtime.odoo.settings") as mock_settings,
    ):
        mock_settings.odoo_url = "https://odoo.example.com"
        mock_settings.odoo_database = "db"
        mock_settings.odoo_username = "u"
        mock_settings.odoo_api_key = "k"
        result = await _run_odoo_sync("tenant-1", limit=50)

    assert result == {"tenant_id": "tenant-1", "limit": 50, "ok": True}
