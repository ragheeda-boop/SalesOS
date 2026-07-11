"""Knowledge Graph Runtime — graph engine for entity relationships and traversal.

Uses Neo4j as primary graph store with automatic pgvector fallback for 
similarity queries. Integrated with the Data Fabric pipeline to 
automatically populate the graph when golden records are created/updated.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


class NodeLabel(str, Enum):
    COMPANY = "Company"
    PERSON = "Person"
    SOURCE = "Source"
    LICENSE = "License"
    BRANCH = "Branch"
    PRODUCT = "Product"
    FUNDING_EVENT = "FundingEvent"
    JOB_POSTING = "JobPosting"
    INTENT_SIGNAL = "IntentSignal"


class EdgeType(str, Enum):
    HAS_LICENSE = "HAS_LICENSE"
    HAS_BRANCH = "HAS_BRANCH"
    HAS_PRODUCT = "HAS_PRODUCT"
    EMPLOYS = "EMPLOYS"
    RECEIVED_FUNDING = "RECEIVED_FUNDING"
    POSTED_JOB = "POSTED_JOB"
    HAS_INTENT = "HAS_INTENT"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    COMPETITOR_OF = "COMPETITOR_OF"
    PARTNER_WITH = "PARTNER_WITH"
    INGESTED_FROM = "INGESTED_FROM"
    CONTACT_OF = "CONTACT_OF"


@dataclass
class GraphNode:
    id: str
    labels: list[NodeLabel]
    properties: dict[str, Any]

    def to_dict(self) -> dict:
        return {"id": self.id, "labels": [l.value for l in self.labels], "properties": self.properties}


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"source": self.source_id, "target": self.target_id, "type": self.type.value, "properties": self.properties}


@dataclass
class GraphPath:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    length: int = 0

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "length": self.length,
        }


@dataclass
class GraphMetrics:
    nodes_created: int = 0
    edges_created: int = 0
    queries_executed: int = 0
    total_query_ms: float = 0.0
    errors: int = 0
    neo4j_available: bool = True
    sync_count: int = 0

    def snapshot(self) -> dict:
        return {
            "nodes_created": self.nodes_created,
            "edges_created": self.edges_created,
            "queries_executed": self.queries_executed,
            "total_query_ms": round(self.total_query_ms, 2),
            "avg_query_ms": round(self.total_query_ms / max(self.queries_executed, 1), 2),
            "errors": self.errors,
            "neo4j_available": self.neo4j_available,
            "sync_count": self.sync_count,
        }


class KnowledgeGraphEngine:
    """Graph engine with Neo4j primary + SQL fallback.

    Population flow (called by Data Fabric pipeline after entity resolution):
      1. upsert_company() — creates/merges Company node with all properties
      2. upsert_related() — creates edges to licenses, branches, products, etc.
      3. infer_relationships() — discovers competitors, subsidiaries

    Query patterns:
      - find_competitors(company_id) → similar companies in same industry/region
      - find_path(source_id, target_id) → shortest path between entities
      - get_ego_network(company_id, depth=2) → neighborhood graph
      - search(query, labels=None) → full-text search on node properties
      - get_decision_makers(company_id) → senior persons at a company
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._logger = logger
        self.metrics = GraphMetrics()
        self._driver = None

        # Try connecting to Neo4j
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    max_connection_pool_size=settings.neo4j_max_connection_pool_size,
                    connection_acquisition_timeout=settings.neo4j_connection_acquisition_timeout,
                    max_transaction_retry_time=settings.neo4j_max_transaction_retry_time,
                )
                self.metrics.neo4j_available = True
                # Create full-text indexes for search
                asyncio.ensure_future(self._ensure_indexes())
            except Exception as exc:
                if self._logger:
                    self._logger.warning("Neo4j connection failed, using SQL fallback: %s", exc)
                self.metrics.neo4j_available = False
        else:
            self.metrics.neo4j_available = False

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def _ensure_indexes(self):
        """Create full-text search indexes on Neo4j for fast search."""
        try:
            async with self._driver.session(database=settings.neo4j_database) as session:
                await session.run("""
                    CREATE FULLTEXT INDEX company_fulltext IF NOT EXISTS
                    FOR (n:COMPANY) ON EACH [n.name_ar, n.name_en, n.cr_number]
                """)
                await session.run("""
                    CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
                    FOR (n:PERSON) ON EACH [n.name_ar, n.name_en, n.position, n.email]
                """)
                if self._logger:
                    self._logger.info("Neo4j full-text indexes created / verified")
        except Exception as exc:
            if self._logger:
                self._logger.warning("Failed to create Neo4j full-text index (fallback to CONTAINS): %s", exc)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ── Node CRUD ───────────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str) -> GraphNode:
        return await self._run(
            "upsert_company",
            self._upsert_company_neo4j,
            self._upsert_company_sql,
            company=company,
            tenant_id=tenant_id,
        )

    async def upsert_person(self, person: dict, tenant_id: str) -> GraphNode:
        return await self._run(
            "upsert_person",
            self._upsert_person_neo4j,
            self._upsert_person_sql,
            person=person,
            tenant_id=tenant_id,
        )

    async def get_node(self, node_id: str, labels: Optional[list[NodeLabel]] = None) -> Optional[GraphNode]:
        return await self._run(
            "get_node",
            self._get_node_neo4j,
            self._get_node_sql,
            node_id=node_id,
            labels=labels,
        )

    # ── Edge CRUD ───────────────────────────────────────────────

    async def create_edge(self, source_id: str, target_id: str, edge_type: EdgeType, properties: Optional[dict] = None) -> GraphEdge:
        return await self._run(
            "create_edge",
            self._create_edge_neo4j,
            self._create_edge_sql,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {},
        )

    # ── Graph Population (batch from golden record) ─────────────

    async def populate_from_golden_record(self, golden_record: dict, tenant_id: str) -> dict:
        """Create/update all graph nodes and edges for a golden record."""
        t0 = time.monotonic()
        stats = {"nodes": 0, "edges": 0}

        company_node = await self.upsert_company(golden_record, tenant_id)
        stats["nodes"] += 1

        company_id = golden_record.get("company_id") or golden_record.get("id")
        if not company_id:
            return stats

        async with self._session_factory() as session:
            # Licenses
            rows = await session.execute(
                sa_text("SELECT * FROM licenses WHERE company_id = :cid"),
                {"cid": company_id},
            )
            for lic in rows.mappings().all():
                lic_node = await self._upsert_license_node(dict(lic), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, lic_node.id, EdgeType.HAS_LICENSE)
                stats["edges"] += 1

            # Branches
            rows = await session.execute(
                sa_text("SELECT * FROM branches WHERE company_id = :cid"),
                {"cid": company_id},
            )
            for branch in rows.mappings().all():
                branch_node = await self._upsert_branch_node(dict(branch), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, branch_node.id, EdgeType.HAS_BRANCH)
                stats["edges"] += 1

            # Contacts
            rows = await session.execute(
                sa_text("SELECT * FROM contacts WHERE company_id = :cid"),
                {"cid": company_id},
            )
            for contact in rows.mappings().all():
                person_node = await self._upsert_person_node(dict(contact), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, person_node.id, EdgeType.EMPLOYS)
                stats["edges"] += 1

        # Infer relationships
        inferred = await self._infer_relationships(company_id, tenant_id)
        stats["edges"] += inferred

        self.metrics.sync_count += 1
        elapsed = (time.monotonic() - t0) * 1000
        if self._logger:
            self._logger.info("Graph populated for company %s: %s (%.0fms)", company_id, stats, elapsed)

        return stats

    # ── Graph Queries ───────────────────────────────────────────

    async def find_competitors(self, company_id: str, tenant_id: str, limit: int = 10) -> list[GraphNode]:
        return await self._run(
            "find_competitors",
            self._find_competitors_neo4j,
            self._find_competitors_sql,
            company_id=company_id,
            tenant_id=tenant_id,
            limit=limit,
        )

    async def find_path(self, source_id: str, target_id: str, max_depth: int = 6) -> Optional[GraphPath]:
        return await self._run(
            "find_path",
            self._find_path_neo4j,
            self._find_path_sql,
            source_id=source_id,
            target_id=target_id,
            max_depth=max_depth,
        )

    async def get_ego_network(self, company_id: str, depth: int = 2) -> list[dict]:
        return await self._run(
            "ego_network",
            self._get_ego_network_neo4j,
            self._get_ego_network_sql,
            company_id=company_id,
            depth=depth,
        )

    async def get_decision_makers(self, company_id: str) -> list[GraphNode]:
        return await self._run(
            "get_decision_makers",
            self._get_decision_makers_neo4j,
            self._get_decision_makers_sql,
            company_id=company_id,
        )

    async def search(self, query: str, labels: Optional[list[NodeLabel]] = None, limit: int = 20) -> list[GraphNode]:
        return await self._run(
            "search",
            self._search_neo4j,
            self._search_sql,
            query=query,
            labels=labels,
            limit=limit,
        )

    # ── Maintenance ─────────────────────────────────────────────

    async def rebuild(self, tenant_id: str) -> dict:
        """Rebuild the entire graph from golden records for a tenant."""
        stats = {"companies": 0, "nodes": 0, "edges": 0}
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("SELECT * FROM golden_records WHERE tenant_id = :tid AND is_active = true"),
                {"tid": tenant_id},
            )
            for row in rows.mappings().all():
                record = dict(row)
                result = await self.populate_from_golden_record(record, tenant_id)
                stats["companies"] += 1
                stats["nodes"] += result["nodes"]
                stats["edges"] += result["edges"]
        return stats

    # ── Internal routing ────────────────────────────────────────

    async def _run(self, op_name: str, neo4j_fn, sql_fn, **kwargs):
        self.metrics.queries_executed += 1
        t0 = time.monotonic()
        try:
            if self.metrics.neo4j_available and self._driver:
                result = await neo4j_fn(**kwargs)
                elapsed = (time.monotonic() - t0) * 1000
                self.metrics.total_query_ms += elapsed
                return result
            result = await sql_fn(**kwargs)
            elapsed = (time.monotonic() - t0) * 1000
            self.metrics.total_query_ms += elapsed
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            self.metrics.errors += 1
            if self._logger:
                self._logger.error("Graph %s error (%.0fms): %s", op_name, elapsed, exc)
            # Fallback to SQL on Neo4j failure
            if self.metrics.neo4j_available:
                try:
                    return await sql_fn(**kwargs)
                except Exception:
                    pass
            raise

    # ── Neo4j implementations ───────────────────────────────────

    async def _upsert_company_neo4j(self, company: dict, tenant_id: str) -> GraphNode:
        async with self._driver.session(database=settings.neo4j_database) as session:
            cid = company.get("company_id") or company.get("id") or str(company.get("cr_number", ""))
            result = await session.run(
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
            record = await result.single()
            self.metrics.nodes_created += 1
            return GraphNode(id=cid, labels=[NodeLabel.COMPANY], properties=company)

    async def _upsert_person_neo4j(self, person: dict, tenant_id: str) -> GraphNode:
        async with self._driver.session(database=settings.neo4j_database) as session:
            pid = person.get("id") or person.get("email", "")
            result = await session.run(
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
            await result.single()
            self.metrics.nodes_created += 1
            return GraphNode(id=pid, labels=[NodeLabel.PERSON], properties=person)

    async def _create_edge_neo4j(self, source_id: str, target_id: str, edge_type: EdgeType, properties: dict) -> GraphEdge:
        async with self._driver.session(database=settings.neo4j_database) as session:
            type_name = edge_type.value
            props_str = ", ".join(f"{k}: ${k}" for k in properties)
            query = f"""
                MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                MERGE (a)-[r:{type_name} {{{props_str}}}]->(b)
                RETURN r
            """
            params = {"source_id": source_id, "target_id": target_id, **properties}
            await session.run(query, **params)
            self.metrics.edges_created += 1
            return GraphEdge(source_id=source_id, target_id=target_id, type=edge_type, properties=properties)

    async def _find_competitors_neo4j(self, company_id: str, tenant_id: str, limit: int = 10) -> list[GraphNode]:
        async with self._driver.session(database=settings.neo4j_database) as session:
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

    async def _find_path_neo4j(self, source_id: str, target_id: str, max_depth: int = 6) -> Optional[GraphPath]:
        async with self._driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH p = shortestPath((a {id: $source_id})-[*..$max_depth]-(b {id: $target_id}))
                RETURN p
                """,
                source_id=source_id,
                target_id=target_id,
                max_depth=max_depth,
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

    async def _get_ego_network_neo4j(self, company_id: str, depth: int = 2) -> list[dict]:
        async with self._driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH (c:Company {id: $id})-[r:*1..$depth]-(neighbor)
                RETURN DISTINCT neighbor, type(r) as rel_type, r as rel
                """,
                id=company_id,
                depth=depth,
            )
            items = []
            async for record in result:
                n = record["neighbor"]
                items.append({
                    "node": GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n)).to_dict(),
                    "relationship": record["rel_type"],
                })
            return items

    async def _get_decision_makers_neo4j(self, company_id: str) -> list[GraphNode]:
        async with self._driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH (c:Company {id: $id})-[:EMPLOYS]->(p:Person)
                WHERE p.position CONTAINS 'CEO' OR p.position CONTAINS 'CTO'
                   OR p.position CONTAINS 'VP' OR p.position CONTAINS 'Director'
                   OR p.position CONTAINS 'Head' OR p.position CONTAINS 'President'
                RETURN p
                """,
                id=company_id,
            )
            nodes = []
            async for record in result:
                n = record["p"]
                nodes.append(GraphNode(id=n["id"], labels=[NodeLabel.PERSON], properties=dict(n)))
            return nodes

    async def _search_neo4j(self, query: str, labels: Optional[list[NodeLabel]], limit: int = 20) -> list[GraphNode]:
        async with self._driver.session(database=settings.neo4j_database) as session:
            try:
                label_filter = ":" + "|".join(l.value for l in labels) if labels else ""
                index_name = "company_fulltext" if (not labels or NodeLabel.COMPANY in labels) else "person_fulltext"
                result = await session.run(
                    f"""
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
                # Fallback to CONTAINS if full-text index doesn't exist
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

    async def _get_node_neo4j(self, node_id: str, labels: Optional[list[NodeLabel]] = None) -> Optional[GraphNode]:
        async with self._driver.session(database=settings.neo4j_database) as session:
            label_filter = ":" + "|".join(l.value for l in labels) if labels else ""
            result = await session.run(
                f"MATCH (n{label_filter} {{id: $id}}) RETURN n",
                id=node_id,
            )
            record = await result.single()
            if not record:
                return None
            n = record["n"]
            return GraphNode(id=n["id"], labels=[NodeLabel.COMPANY], properties=dict(n))

    # ── Node creation helpers (edge upserts) ────────────────────

    async def _upsert_license_node(self, lic: dict, tenant_id: str) -> GraphNode:
        lid = lic.get("id") or lic.get("license_number", "")
        async with self._session_factory() as session:
            if self.metrics.neo4j_available and self._driver:
                async with self._driver.session(database=settings.neo4j_database) as neo4j_session:
                    await neo4j_session.run(
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

    async def _upsert_branch_node(self, branch: dict, tenant_id: str) -> GraphNode:
        bid = branch.get("id", "")
        async with self._session_factory() as session:
            if self.metrics.neo4j_available and self._driver:
                async with self._driver.session(database=settings.neo4j_database) as neo4j_session:
                    await neo4j_session.run(
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

    async def _upsert_person_node(self, contact: dict, tenant_id: str) -> GraphNode:
        pid = contact.get("id") or contact.get("email", "")
        return await self._upsert_person_neo4j(contact, tenant_id)

    # ── Relationship inference ──────────────────────────────────

    async def _infer_relationships(self, company_id: str, tenant_id: str) -> int:
        """Discover and create inferred edges (competitors, subsidiaries)."""
        count = 0
        async with self._session_factory() as session:
            # Get company details
            row = await session.execute(
                sa_text("SELECT industry, city FROM companies WHERE id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            company = row.mappings().one_or_none()
            if not company:
                return 0

            # Find competitors: same industry + same city
            if company.get("industry") or company.get("city"):
                comps = await session.execute(
                    sa_text("""
                        SELECT id FROM companies
                        WHERE tenant_id = :tid AND id != :cid
                          AND (industry = :industry OR city = :city)
                        LIMIT 20
                    """),
                    {"tid": tenant_id, "cid": company_id,
                     "industry": company.get("industry", ""),
                     "city": company.get("city", "")},
                )
                for comp in comps.mappings().all():
                    await self.create_edge(company_id, comp["id"], EdgeType.COMPETITOR_OF)
                    count += 1

            # Find subsidiaries: parent_company_id
            subs = await session.execute(
                sa_text("SELECT id FROM companies WHERE parent_company_id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            for sub in subs.mappings().all():
                await self.create_edge(company_id, sub["id"], EdgeType.SUBSIDIARY_OF)
                count += 1

        return count

    # ── SQL fallback implementations ────────────────────────────

    async def _upsert_company_sql(self, company: dict, tenant_id: str) -> GraphNode:
        cid = company.get("company_id") or company.get("id") or company.get("cr_number", "")
        return GraphNode(id=cid, labels=[NodeLabel.COMPANY], properties=company)

    async def _upsert_person_sql(self, person: dict, tenant_id: str) -> GraphNode:
        pid = person.get("id") or person.get("email", "")
        return GraphNode(id=pid, labels=[NodeLabel.PERSON], properties=person)

    async def _create_edge_sql(self, source_id: str, target_id: str, edge_type: EdgeType, properties: dict) -> GraphEdge:
        async with self._session_factory() as session:
            await session.execute(
                sa_text("""
                    INSERT INTO graph_edges (source_id, target_id, edge_type, properties)
                    VALUES (:src, :tgt, :type, :props)
                    ON CONFLICT (source_id, target_id, edge_type) DO NOTHING
                """),
                {"src": source_id, "tgt": target_id, "type": edge_type.value, "props": properties},
            )
            await session.commit()
        return GraphEdge(source_id=source_id, target_id=target_id, type=edge_type, properties=properties)

    async def _find_competitors_sql(self, company_id: str, tenant_id: str, limit: int = 10) -> list[GraphNode]:
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT * FROM graph_edges
                    WHERE (source_id = :cid OR target_id = :cid)
                      AND edge_type = 'COMPETITOR_OF'
                    LIMIT :lim
                """),
                {"cid": company_id, "lim": limit},
            )
            nodes = []
            for row in rows.mappings().all():
                neighbor_id = row["target_id"] if row["source_id"] == company_id else row["source_id"]
                nodes.append(GraphNode(id=neighbor_id, labels=[NodeLabel.COMPANY], properties={}))
            return nodes

    async def _find_path_sql(self, source_id: str, target_id: str, max_depth: int = 6) -> Optional[GraphPath]:
        # Simple SQL fallback — only direct edges
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("""
                    SELECT * FROM graph_edges
                    WHERE (source_id = :src AND target_id = :tgt)
                       OR (source_id = :tgt AND target_id = :src)
                    LIMIT 1
                """),
                {"src": source_id, "tgt": target_id},
            )
            edge = row.mappings().one_or_none()
            if not edge:
                return None
            return GraphPath(
                nodes=[
                    GraphNode(id=source_id, labels=[NodeLabel.COMPANY], properties={}),
                    GraphNode(id=target_id, labels=[NodeLabel.COMPANY], properties={}),
                ],
                edges=[GraphEdge(
                    source_id=edge["source_id"],
                    target_id=edge["target_id"],
                    type=EdgeType(edge["edge_type"]),
                )],
                length=1,
            )

    async def _get_ego_network_sql(self, company_id: str, depth: int = 2) -> list[dict]:
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT * FROM graph_edges
                    WHERE source_id = :cid OR target_id = :cid
                    LIMIT 50
                """),
                {"cid": company_id},
            )
            items = []
            for row in rows.mappings().all():
                neighbor_id = row["target_id"] if row["source_id"] == company_id else row["source_id"]
                items.append({
                    "node": GraphNode(id=neighbor_id, labels=[NodeLabel.COMPANY], properties={}).to_dict(),
                    "relationship": row["edge_type"],
                })
            return items

    async def _get_decision_makers_sql(self, company_id: str) -> list[GraphNode]:
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT * FROM contacts
                    WHERE company_id = :cid
                      AND (position ILIKE '%CEO%' OR position ILIKE '%CTO%'
                        OR position ILIKE '%VP%' OR position ILIKE '%Director%'
                        OR position ILIKE '%Head%' OR position ILIKE '%President%')
                """),
                {"cid": company_id},
            )
            return [
                GraphNode(id=r["id"], labels=[NodeLabel.PERSON], properties=dict(r))
                for r in rows.mappings().all()
            ]

    async def _search_sql(self, query: str, labels: Optional[list[NodeLabel]], limit: int = 20) -> list[GraphNode]:
        async with self._session_factory() as session:
            like = f"%{query}%"
            rows = await session.execute(
                sa_text("""
                    SELECT id, name_ar, name_en, cr_number, industry, city
                    FROM companies
                    WHERE name_ar ILIKE :q OR name_en ILIKE :q OR cr_number ILIKE :q
                    LIMIT :lim
                """),
                {"q": like, "lim": limit},
            )
            return [
                GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r))
                for r in rows.mappings().all()
            ]

    async def _get_node_sql(self, node_id: str, labels: Optional[list[NodeLabel]] = None) -> Optional[GraphNode]:
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("SELECT * FROM companies WHERE id = :id"),
                {"id": node_id},
            )
            r = row.mappings().one_or_none()
            if not r:
                return None
            return GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r))
