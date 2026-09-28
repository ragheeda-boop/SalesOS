"""AgentContextCollector.collect() used asyncio.run() internally to bridge
to its runtime dependencies' async methods (timeline_runtime.query(),
feature_store.get_scores(), kg_engine.get_ego_network()) -- but collect()
itself was a plain synchronous method. Every real caller of this SDK
already runs inside a live asyncio event loop (this is a FastAPI
application) -- asyncio.run() cannot be called from within an already-
running loop, so all three calls raised RuntimeError unconditionally the
moment this is ever invoked from real request-handling code. The failure
was invisible: each call site's own `except Exception: pass` silently
swallowed it, leaving timeline/features/graph permanently empty regardless
of what the underlying runtimes would have returned.

Same bug class as report 136's Odoo sync fix (runtime/odoo/__init__.py):
a sync wrapper calling asyncio.run() from code that will always itself be
called from within a running loop. Fixed the same way: collect() is now a
real `async def`, awaiting its dependencies directly instead of bridging
through asyncio.run().

Reproduced directly (not asserted) before writing the fix: calling the
original sync collect() from inside asyncio.run(main()) -- exactly how any
real FastAPI request handler would invoke it -- returned an empty timeline
even though the fake runtime below returns real data when awaited
correctly.
"""

from __future__ import annotations

import pytest

from sdk.agent_sdk import AgentContextCollector


class _FakeTimelineRuntime:
    async def query(self, entity_type: str, entity_id: str, limit: int) -> list[dict]:
        return [{"event": "created", "entity_id": entity_id}]


class _FakeFeatureStore:
    async def get_scores(self, entity_id: str) -> dict:
        return {"icp": 0.8, "intent": 0.6}


class _FakeKnowledgeGraph:
    async def get_ego_network(self, entity_id: str, depth: int) -> dict:
        return {"nodes": [entity_id], "edges": []}


@pytest.mark.asyncio
async def test_collect_populates_timeline_features_and_graph_from_a_real_running_loop() -> None:
    """This test itself runs inside pytest-asyncio's event loop -- exactly
    the "already running loop" condition that broke the old asyncio.run()
    based implementation. If collect() ever regresses to using
    asyncio.run() internally, this fails with RuntimeError."""
    collector = AgentContextCollector(
        {
            "timeline_runtime": _FakeTimelineRuntime(),
            "feature_store": _FakeFeatureStore(),
            "kg_engine": _FakeKnowledgeGraph(),
        }
    )

    ctx = await collector.collect(
        user_id="u1", tenant_id="t1", entity_type="company", entity_id="c1"
    )

    assert ctx.timeline == [{"event": "created", "entity_id": "c1"}]
    assert ctx.features == {"icp": 0.8, "intent": 0.6}
    assert ctx.graph == {"nodes": ["c1"], "edges": []}
    assert ctx.entity_data == {"type": "company", "id": "c1"}


@pytest.mark.asyncio
async def test_collect_degrades_gracefully_when_no_runtimes_are_registered() -> None:
    collector = AgentContextCollector({})

    ctx = await collector.collect(user_id="u1", tenant_id="t1")

    assert ctx.timeline == []
    assert ctx.features == {}
    assert ctx.graph is None
