"""Neo4j graph database abstraction."""

from __future__ import annotations

import asyncio
import random
import re
from contextlib import asynccontextmanager
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j import AsyncDriver, AsyncManagedTransaction, Record

from sdk.config import sdk_settings

_NEO4J_MAX_RETRIES = 3
_NEO4J_RETRY_BASE_DELAY = 0.1

_CYpher_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _validate_cypher_identifier(name: str, kind: str = "identifier") -> str:
    """Validate a Cypher identifier (label, relationship type, property key)."""
    if not _CYpher_IDENT_RE.match(name):
        raise ValueError(f"Invalid Cypher {kind}: {name!r}")
    return name


class GraphService:
    """Neo4j graph database service for knowledge graph operations.

    All graph operations go through this service rather than
    accessing Neo4j directly from modules.
    """

    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    @asynccontextmanager
    async def _session(self):
        async with self._driver.session(
            database=sdk_settings.neo4j_database,
            max_transaction_retry_time=sdk_settings.neo4j_max_transaction_retry_time,
        ) as session:
            yield session

    @asynccontextmanager
    async def _transaction(self):
        async with self._driver.session() as session:
            async with await session.begin_transaction() as tx:
                yield tx

    async def _run(self, op_name: str, fn, **kwargs):
        last_error = None
        for attempt in range(1, _NEO4J_MAX_RETRIES + 1):
            try:
                return await fn(**kwargs)
            except Exception as exc:
                last_error = exc
                if attempt < _NEO4J_MAX_RETRIES:
                    delay = _NEO4J_RETRY_BASE_DELAY * (2 ** (attempt - 1)) * (1 + random.random() * 0.1)
                    await asyncio.sleep(delay)
        raise last_error

    async def health_check(self) -> bool:
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def create_node(
        self,
        labels: list[str],
        properties: dict[str, Any],
    ) -> str | None:
        async def _create():
            validated = [_validate_cypher_identifier(l, "label") for l in labels]
            label_str = ":".join(validated)
            async with self._driver.session() as session:
                label_str = ":".join(labels)
                result = await session.run(
                    f"CREATE (n:{label_str} $props) RETURN elementId(n) AS id",
                    props=properties,
                )
                record = await result.single()
                return record["id"] if record else None
        return await self._run("create_node", _create)

    async def find_node(self, node_type: str, property_key: str, property_value: str) -> dict | None:
        async def _find():
            _validate_cypher_identifier(node_type, "label")
            _validate_cypher_identifier(property_key, "property")
            async with self._driver.session() as session:
                result = await session.run(
                    f"MATCH (n:{node_type} {{{property_key}: $value}}) RETURN n, elementId(n) AS id",
                    value=property_value,
                )
                record = await result.single()
                if record:
                    node = record["n"]
                    return {**dict(node), "_id": record["id"]}
                return None
        return await self._run("find_node", _find)

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        async def _create_rel():
            _validate_cypher_identifier(rel_type, "relationship type")
            async with self._driver.session() as session:
                await session.run(
                    f"""
                    MATCH (a) WHERE elementId(a) = $from_id
                    MATCH (b) WHERE elementId(b) = $to_id
                    CREATE (a)-[r:{rel_type} $props]->(b)
                    """,
                    from_id=from_id,
                    to_id=to_id,
                    props=properties or {},
                )
        return await self._run("create_relationship", _create_rel)

    async def find_related(
        self,
        node_id: str,
        rel_type: str | None = None,
        direction: str = "outgoing",
    ) -> list[dict]:
        async def _find_rel():
            direction_symbol = "-" if direction == "outgoing" else "<-"
            rel_pattern = f"[r:{rel_type}]" if rel_type else "[r]"
            if rel_type:
                _validate_cypher_identifier(rel_type, "relationship type")
            query = f"""
                MATCH (a){direction_symbol}{rel_pattern}-(b)
                WHERE elementId(a) = $node_id
                RETURN b, elementId(b) AS id, type(r) AS relationship, r AS rel_props
            """
            async with self._driver.session() as session:
                result = await session.run(query, node_id=node_id)
                return await result.data()
        return await self._run("find_related", _find_rel)

    async def shortest_path(
        self, from_type: str, from_key: str, from_value: str,
        to_type: str, to_key: str, to_value: str,
        max_hops: int = 6,
    ) -> list[dict] | None:
        async def _path():
            _validate_cypher_identifier(from_type, "label")
            _validate_cypher_identifier(from_key, "property")
            _validate_cypher_identifier(to_type, "label")
            _validate_cypher_identifier(to_key, "property")
            query = f"""
                MATCH path = shortestPath(
                    (a:{from_type} {{{from_key}: $from_value}})-[*..{max_hops}]-(b:{to_type} {{{to_key}: $to_value}})
                )
                RETURN [node IN nodes(path) | {{id: elementId(node), labels: labels(node), properties: properties(node)}}] AS nodes,
                       [rel IN relationships(path) | {{type: type(rel), properties: properties(rel)}}] AS relationships
            """
            async with self._driver.session() as session:
                result = await session.run(
                    query,
                    from_value=from_value,
                    to_value=to_value,
                )
                record = await result.single()
                return dict(record) if record else None
        return await self._run("shortest_path", _path)

    async def run_community_detection(self, label: str = "Company") -> list[dict]:
        async def _community():
            _validate_cypher_identifier(label, "label")
            query = f"""
                CALL gds.louvain.stream({{
                    nodeProjection: '{label}',
                    relationshipProjection: {{
                        ALL: {{
                            type: '*',
                            orientation: 'UNDIRECTED',
                            aggregation: 'SINGLE'
                        }}
                    }}
                }})
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id AS company_id, communityId
                ORDER BY communityId
            """
            async with self._driver.session() as session:
                result = await session.run(query)
                return await result.data()
        return await self._run("community_detection", _community)

    async def close(self) -> None:
        try:
            await self._driver.close()
        except Exception:
            pass
