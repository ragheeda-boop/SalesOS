"""Neo4j graph database abstraction."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j import AsyncDriver, AsyncManagedTransaction, Record


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
            database="neo4j",
            max_transaction_retry_time=10,
        ) as session:
            yield session

    @asynccontextmanager
    async def _transaction(self):
        async with self._driver.session() as session:
            async with await session.begin_transaction() as tx:
                yield tx

    async def create_node(
        self,
        labels: list[str],
        properties: dict[str, Any],
    ) -> str | None:
        async with self._driver.session() as session:
            label_str = ":".join(labels)
            result = await session.run(
                f"CREATE (n:{label_str} $props) RETURN elementId(n) AS id",
                props=properties,
            )
            record = await result.single()
            return record["id"] if record else None

    async def find_node(self, node_type: str, property_key: str, property_value: str) -> dict | None:
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

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
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

    async def find_related(
        self,
        node_id: str,
        rel_type: str | None = None,
        direction: str = "outgoing",
    ) -> list[dict]:
        direction_symbol = "-" if direction == "outgoing" else "<-"
        rel_pattern = f"[r:{rel_type}]" if rel_type else "[r]"

        query = f"""
            MATCH (a){direction_symbol}{rel_pattern}-(b)
            WHERE elementId(a) = $node_id
            RETURN b, elementId(b) AS id, type(r) AS relationship, r AS rel_props
        """

        async with self._driver.session() as session:
            result = await session.run(query, node_id=node_id)
            records = await result.data()
            return records

    async def shortest_path(
        self, from_type: str, from_key: str, from_value: str,
        to_type: str, to_key: str, to_value: str,
        max_hops: int = 6,
    ) -> list[dict] | None:
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

    async def run_community_detection(self, label: str = "Company") -> list[dict]:
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

    async def close(self) -> None:
        await self._driver.close()
