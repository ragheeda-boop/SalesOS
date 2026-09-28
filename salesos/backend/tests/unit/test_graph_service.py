"""Tests for sdk.graph.GraphService's Cypher-injection guards.

GraphService (Neo4j abstraction) has zero live callers anywhere in the app
-- Neo4j is deliberately kept offline per ADR-108 -- and had zero prior test
coverage. Every dynamic value f-string-interpolated into a Cypher query
(labels, relationship types, property keys) is already validated via
_validate_cypher_identifier(), EXCEPT shortest_path()'s `max_hops`, which
has no bound-parameter form in Cypher's variable-length path syntax
([*..N]) and was interpolated unchecked. A caller passing a non-int or
malicious string for max_hops (e.g. from user input, the moment this
module is ever wired to a real caller) would have that string land
directly inside the query text.

Fixed with _validate_hop_count(): rejects non-int and out-of-range values
before they ever reach the f-string. This test proves the guard actually
runs before query construction, using a fake Neo4j driver so no real
database is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sdk.graph import GraphService, _validate_hop_count


class _FakeResult:
    def __init__(self, record=None):
        self._record = record

    async def single(self):
        return self._record

    async def data(self):
        return []


class _FakeSession:
    def __init__(self):
        self.run = AsyncMock(return_value=_FakeResult(record={"a": 1}))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeDriver:
    def __init__(self):
        self._session = _FakeSession()

    def session(self, **kwargs):
        return self._session


@pytest.mark.parametrize(
    "bad_value",
    ["6; MATCH (n) DETACH DELETE n //", "6 OR 1=1", 3.5, True, None, [], {}],
)
def test_validate_hop_count_rejects_non_int_and_injection_attempts(bad_value) -> None:
    with pytest.raises(ValueError):
        _validate_hop_count(bad_value)


@pytest.mark.parametrize("bad_value", [0, -1, 16, 1000])
def test_validate_hop_count_rejects_out_of_range(bad_value) -> None:
    with pytest.raises(ValueError):
        _validate_hop_count(bad_value)


def test_validate_hop_count_accepts_valid_range() -> None:
    for value in (1, 6, 15):
        assert _validate_hop_count(value) == value


@pytest.mark.asyncio
async def test_shortest_path_rejects_malicious_max_hops_before_querying() -> None:
    """The malicious value must never reach the driver's .run() call at all."""
    driver = _FakeDriver()
    service = GraphService(driver=driver)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await service.shortest_path(
            from_type="Company",
            from_key="id",
            from_value="c-1",
            to_type="Company",
            to_key="id",
            to_value="c-2",
            max_hops="6; MATCH (n) DETACH DELETE n //",  # type: ignore[arg-type]
        )

    assert not driver._session.run.called, (
        "the malicious max_hops value reached session.run() -- "
        "it should have been rejected before query construction"
    )


@pytest.mark.asyncio
async def test_shortest_path_interpolates_validated_hop_count_correctly() -> None:
    driver = _FakeDriver()
    service = GraphService(driver=driver)  # type: ignore[arg-type]

    await service.shortest_path(
        from_type="Company",
        from_key="id",
        from_value="c-1",
        to_type="Company",
        to_key="id",
        to_value="c-2",
        max_hops=4,
    )

    assert driver._session.run.called
    query_text = driver._session.run.call_args.args[0]
    assert "[*..4]" in query_text
