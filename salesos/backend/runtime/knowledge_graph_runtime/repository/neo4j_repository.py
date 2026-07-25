"""Neo4j-backed graph repository implementation."""

from __future__ import annotations

import re
from typing import Any, Optional

from app.config import settings

from ..models import EdgeType, GraphEdge, GraphNode, GraphPath, NodeLabel
from .base import GraphRepository
from .query_builders import _validate_cypher_identifier, build_tenant_filter

_CYPHER_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


class Neo4jGraphRepository(GraphRepository):
    """Graph repository backed by Neo4j async driver."""

    def __init__(self, driver: Any, logger: Any = None, database: Optional[str] = None):
        self._driver = driver
        self._logger = logger
        self._database = database or settings.neo4j_database

    # ── Index management ────────────────────────────────────────

    async def ensure_indexes(self) -> None:
        if not self._driver:
            return
        try:
            async with self._driver.session(database=self._database) as session:
                await session.run("""
                    CREATE FULLTEXT INDEX company_fulltext IF NOT EXISTS
                    FOR (n:Company) ON EACH [n.name_ar, n.name_en, n.cr_number]
                """)
                await session.run("""
                    CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
                    FOR (n:Person) ON EACH [n.name_ar, n.name_en, n.position, n.email]
                """)
                if self._logger:
                    self._logger.info("Neo4j full-text indexes created / verified")
        except Exception as exc:
            if self._logger:
                self._logger.warning("Failed to create Neo4j full-text index (fallback to CONTAINS): %s", exc)

    # ── Node operations ─────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str = "") -> GraphNode:
        async with self._driver.session(database=self._database) as session:
            cid = company.get("company_id") or company.get("id") or str(company.get("cr_number", ""))
            await session.run(
                """
                MERGE (c:Company {id: $id})
                SET c.tenant_id = $tenant_id,
                    c.name_ar = $name_ar,
                    c.name_en = $name_en,
                    c.cr_number = $cr_number,
                    c.industry = $industry,
                    c.city = $city,
                    c.region = $region,
                    c.status = $status,
                    c.updated_at = datetime()
                RETURN c
                """,
                id=cid,
                tenant_id=tenant_id,
                name_ar=company.get("name_ar", ""),
                name_en=company.get("name_en", ""),
                cr_number=company.get("cr_number", ""),
                industry=company.get("industry", ""),
                city=company.get("city", ""),
                region=company.get("region", ""),
                status=company.get("status", "active"),
            )
            return GraphNode(id=cid, labels=[NodeLabel.COMPANY], properties=company)

    async def upsert_person(self, person: dict, tenant_id: str = "") -> GraphNode:
        async with self._driver.session(database=self._database) as session:
            pid = person.get("id") or person.get("email", "")
            await session.run(
                """
                MERGE (p:Person {id: $id})
                SET p.tenant_id = $tenant_id,
                    p.name = $name,
                    p.email = $email,
                    p.phone = $phone,
                    p.position = $position,
                    p.updated_at = datetime()
                RETURN p
                """,
                id=pid,
                tenant_id=tenant_id,
                name=person.get("name", ""),
                email=person.get("email", ""),
                phone=person.get("phone", ""),
                position=person.get("position", ""),
            )
            return GraphNode(id=pid, labels=[NodeLabel.PERSON], properties=person)

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: dict,
        tenant_id: str = "",
    ) -> GraphEdge:
        async with self._driver.session(database=self._database) as session:
            type_name = edge_type.value
            validated_keys = [_validate_cypher_identifier(k, "property") for k in properties]
            props_str = ", ".join(f"{k}: ${k}" for k in validated_keys)
            query = f"""
                MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                MERGE (a)-[r:{type_name} {{{props_str}}}]->(b)
                RETURN r
            """
            params = {"source_id": source_id, "target_id": target_id, **properties}
            await session.run(query, **params)
            return GraphEdge(source_id=source_id, target_id=target_id, type=edge_type, properties=properties)

    async def get_node(
        self,
        node_id: str,
        labels: Optional[list[NodeLabel]] = None,
        tenant_id: str = "",
    ) -> Optional[GraphNode]:
        async with self._driver.session(database=self._database) as session:
            label_filter = ":" + "|".join(l.value for l in labels) if labels else ""
            tfilter = build_tenant_filter(tenant_id)
            params = {"id": node_id}
            if tenant_id:
                params["tenant_id"] = tenant_id
            result = await session.run(
                f"MATCH (n{label_filter} {tfilter} {{id: $id}}) RETURN n",
                **params,
            )
            record = await result.single()
            if not record:
                return None
            n = record["n"]
            return GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n))

    # ── Graph traversal ─────────────────────────────────────────

    async def find_competitors(
        self, company_id: str, tenant_id: str = "", limit: int = 10
    ) -> list[GraphNode]:
        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                """
                MATCH (c:Company {id: $id})
                MATCH (comp:Company {tenant_id: $tenant_id})
                WHERE comp.id <> $id
                  AND (comp.industry = c.industry OR comp.city = c.city)
                RETURN comp
                LIMIT $limit
                """,
                id=company_id,
                tenant_id=tenant_id,
                limit=limit,
            )
            nodes = []
            async for record in result:
                n = record["comp"]
                nodes.append(GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n)))
            return nodes

    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 6, tenant_id: str = ""
    ) -> Optional[GraphPath]:
        async with self._driver.session(database=self._database) as session:
            tfilter = build_tenant_filter(tenant_id)
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "max_depth": max_depth,
            }
            if tenant_id:
                params["tenant_id"] = tenant_id
            result = await session.run(
                f"""
                MATCH p = shortestPath((a {tfilter} {{id: $source_id}})-[*..$max_depth]-(b {tfilter} {{id: $target_id}}))
                RETURN p
                """,
                **params,
            )
            record = await result.single()
            if not record:
                return None
            path = record["p"]
            nodes = [GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n)) for n in path.nodes]
            edges = [GraphEdge(
                source_id=r.start_node["id"],
                target_id=r.end_node["id"],
                type=EdgeType(r.type),
            ) for r in path.relationships]
            return GraphPath(nodes=nodes, edges=edges, length=len(edges))

    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        async with self._driver.session(database=self._database) as session:
            tfilter = build_tenant_filter(tenant_id)
            params = {"id": company_id, "depth": depth}
            if tenant_id:
                params["tenant_id"] = tenant_id
            result = await session.run(
                f"""
                MATCH (c:Company {tfilter} {{id: $id}})-[r:*1..$depth]-(neighbor)
                RETURN DISTINCT neighbor, type(r) as rel_type, r as rel
                """,
                **params,
            )
            items = []
            async for record in result:
                n = record["neighbor"]
                items.append({
                    "node": GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n)).to_dict(),
                    "relationship": record["rel_type"],
                })
            return items

    async def get_decision_makers(
        self, company_id: str, tenant_id: str = ""
    ) -> list[GraphNode]:
        async with self._driver.session(database=self._database) as session:
            tfilter = build_tenant_filter(tenant_id)
            params = {"id": company_id}
            if tenant_id:
                params["tenant_id"] = tenant_id
            result = await session.run(
                f"""
                MATCH (c:Company {tfilter} {{id: $id}})-[:EMPLOYS]->(p:Person)
                WHERE p.position CONTAINS 'CEO' OR p.position CONTAINS 'CTO'
                   OR p.position CONTAINS 'VP' OR p.position CONTAINS 'Director'
                   OR p.position CONTAINS 'Head' OR p.position CONTAINS 'President'
                RETURN p
                """,
                **params,
            )
            nodes = []
            async for record in result:
                n = record["p"]
                nodes.append(GraphNode(id=n["id"], labels=[NodeLabel.PERSON], properties=dict(n)))
            return nodes

    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        async with self._driver.session(database=self._database) as session:
            try:
                index_name = "company_fulltext" if (not labels or NodeLabel.COMPANY in labels) else "person_fulltext"
                result = await session.run(
                    """
                    CALL db.index.fulltext.queryNodes($index, $query)
                    YIELD node, score
                    RETURN node
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    index=index_name,
                    query=f"{query}~",
                    limit=limit,
                )
                nodes = []
                async for record in result:
                    n = record["node"]
                    nodes.append(GraphNode(id=n["id"], labels=list(n.labels), properties=dict(n)))
                return nodes
            except Exception:
                label_filter = ":" + "|".join(l.value for l in labels) if labels else ""
                result = await session.run(
                    f"""
                    MATCH (n{label_filter})
                    WHERE n.name_ar CONTAINS $query OR n.name_en CONTAINS $query
                       OR n.cr_number CONTAINS $query
                    RETURN n
                    LIMIT $limit
                    """,
                    query=query,
                    limit=limit,
                )
                nodes = []
                async for record in result:
                    n = record["n"]
                    nodes.append(GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n)))
                return nodes

    # ── Entity operations ───────────────────────────────────────

    async def upsert_license(self, lic: dict, tenant_id: str = "") -> GraphNode:
        lid = lic.get("id") or lic.get("license_number", "")
        async with self._driver.session(database=self._database) as session:
            await session.run(
                """
                MERGE (l:License {id: $id})
                SET l.tenant_id = $tenant_id,
                    l.license_number = $number,
                    l.license_type = $type,
                    l.status = $status,
                    l.updated_at = datetime()
                """,
                id=lid,
                tenant_id=tenant_id,
                number=lic.get("license_number", ""),
                type=lic.get("license_type", ""),
                status=lic.get("status", "active"),
            )
        return GraphNode(id=lid, labels=[NodeLabel.LICENSE], properties=lic)

    async def upsert_branch(self, branch: dict, tenant_id: str = "") -> GraphNode:
        bid = branch.get("id", "")
        async with self._driver.session(database=self._database) as session:
            await session.run(
                """
                MERGE (b:Branch {id: $id})
                SET b.tenant_id = $tenant_id,
                    b.name_ar = $name_ar,
                    b.city = $city,
                    b.updated_at = datetime()
                """,
                id=bid,
                tenant_id=tenant_id,
                name_ar=branch.get("name_ar", ""),
                city=branch.get("city", ""),
            )
        return GraphNode(id=bid, labels=[NodeLabel.BRANCH], properties=branch)

    async def get_entity_subgraph(
        self, entity_id: str, depth: int = 2, tenant_id: str = ""
    ) -> dict:
        async with self._driver.session(database=self._database) as session:
            tfilter = build_tenant_filter(tenant_id)
            params = {"id": entity_id, "depth": depth}
            if tenant_id:
                params["tenant_id"] = tenant_id
            result = await session.run(
                f"""
                MATCH (center {tfilter} {{id: $id}})-[r*1..$depth]-(neighbor)
                WITH center, r, neighbor
                RETURN DISTINCT neighbor AS node,
                       [rel IN r | {{type: type(rel), source: startNode(rel).id, target: endNode(rel).id}}] AS rels
                UNION
                MATCH (center {tfilter} {{id: $id}})
                RETURN center AS node, [] AS rels
                """,
                **params,
            )
            seen_nodes: dict[str, dict] = {}
            seen_edges: dict[str, dict] = {}
            async for record in result:
                n = record["node"]
                nid = n.get("id", "")
                if nid not in seen_nodes:
                    seen_nodes[nid] = {
                        "id": nid,
                        "labels": list(n.labels),
                        "properties": dict(n),
                    }
                for rel in record.get("rels", []):
                    edge_key = f"{rel['source']}->{rel['target']}:{rel['type']}"
                    if edge_key not in seen_edges:
                        seen_edges[edge_key] = {
                            "source": rel["source"],
                            "target": rel["target"],
                            "type": rel["type"],
                        }
            return {
                "nodes": list(seen_nodes.values()),
                "edges": list(seen_edges.values()),
            }

    async def merge_graph_nodes(
        self, surviving_id: str, absorbed_id: str, tenant_id: str = ""
    ) -> dict:
        stats = {"edges_rewired": 0, "node_deleted": False}
        tfilter = build_tenant_filter(tenant_id)
        params = {
            "surviving_id": surviving_id,
            "absorbed_id": absorbed_id,
        }
        if tenant_id:
            params["tenant_id"] = tenant_id
        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                f"""
                MATCH (a {tfilter} {{id: $absorbed}})-[r]->(b)
                WHERE NOT (a {{id: $surviving}})-[]->(b)
                MERGE (s {tfilter} {{id: $surviving}})-[r2:REWIRED]->(b)
                DELETE r
                RETURN count(r2) AS rewired
                """,
                surviving_id=surviving_id,
                absorbed_id=absorbed_id,
                tenant_id=tenant_id,
            )
            record = await result.single()
            stats["edges_rewired"] = record["rewired"] if record else 0

            result2 = await session.run(
                f"""
                MATCH (a)-[r]->(b {tfilter} {{id: $absorbed}})
                WHERE NOT (a)-[]->(s {tfilter} {{id: $surviving}})
                MERGE (a)-[r2:REWIRED]->(s {tfilter} {{id: $surviving}})
                DELETE r
                RETURN count(r2) AS rewired
                """,
                surviving_id=surviving_id,
                absorbed_id=absorbed_id,
                tenant_id=tenant_id,
            )
            record2 = await result2.single()
            stats["edges_rewired"] += record2["rewired"] if record2 else 0

            result3 = await session.run(
                f"MATCH (n {tfilter} {{id: $id}}) DETACH DELETE n RETURN count(n) AS deleted",
                id=absorbed_id,
                tenant_id=tenant_id,
            )
            record3 = await result3.single()
            stats["node_deleted"] = (record3["deleted"] if record3 else 0) > 0
        return stats
