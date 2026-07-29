"""Knowledge Graph service — business logic and coordination layer."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from .models import EdgeType, GraphEdge, GraphMetrics, GraphNode, GraphPath, NodeLabel
from .repository import (
    Neo4jGraphRepository,
    RouterGraphRepository,
    SqlGraphRepository,
)


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

        sql_repo = SqlGraphRepository(session_factory=session_factory, logger=logger)

        neo4j_repo: Optional[Neo4jGraphRepository] = None
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    max_connection_pool_size=settings.neo4j_max_connection_pool_size,
                    connection_acquisition_timeout=settings.neo4j_connection_acquisition_timeout,
                    max_transaction_retry_time=settings.neo4j_max_transaction_retry_time,
                    max_connection_lifetime=1800,
                )
                neo4j_repo = Neo4jGraphRepository(driver=self._driver, logger=logger)
                asyncio.ensure_future(self._verify_driver_connectivity())
                self.metrics.neo4j_available = True
                asyncio.ensure_future(neo4j_repo.ensure_indexes())
            except Exception as exc:
                if self._logger:
                    self._logger.warning("Neo4j connection failed, using SQL fallback: %s", exc)
                self.metrics.neo4j_available = False
        else:
            self.metrics.neo4j_available = False

        self.repo = RouterGraphRepository(
            primary=neo4j_repo,
            fallback=sql_repo,
            metrics=self.metrics,
            logger=logger,
        )

    async def close(self):
        if self._driver:
            try:
                await self._driver.close()
            except Exception:
                pass
            self._driver = None

    async def _verify_driver_connectivity(self):
        try:
            async with self._driver.session(database=settings.neo4j_database) as session:
                await session.run("RETURN 1")
            self.metrics.neo4j_available = True
        except Exception:
            self.metrics.neo4j_available = False
            if self._logger:
                self._logger.warning("Neo4j connectivity verification failed, using SQL fallback")

    async def health_check(self) -> bool:
        if not self._driver:
            self.metrics.neo4j_available = False
            return False
        try:
            await self._driver.verify_connectivity()
            if not self.metrics.neo4j_available:
                if self._logger:
                    self._logger.info("Neo4j connection pool restored")
            self.metrics.neo4j_available = True
            return True
        except Exception as exc:
            if self.metrics.neo4j_available:
                if self._logger:
                    self._logger.warning("Neo4j health check failed: %s", exc)
            self.metrics.neo4j_available = False
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ── Node CRUD ───────────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str) -> GraphNode:
        node = await self.repo.upsert_company(company=company, tenant_id=tenant_id)
        self.metrics.nodes_created += 1
        return node

    async def upsert_person(self, person: dict, tenant_id: str) -> GraphNode:
        node = await self.repo.upsert_person(person=person, tenant_id=tenant_id)
        self.metrics.nodes_created += 1
        return node

    async def get_node(
        self, node_id: str, labels: Optional[list[NodeLabel]] = None, tenant_id: str = ""
    ) -> Optional[GraphNode]:
        return await self.repo.get_node(node_id=node_id, labels=labels, tenant_id=tenant_id)

    # ── Edge CRUD ───────────────────────────────────────────────

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: Optional[dict] = None,
        tenant_id: str = "",
    ) -> GraphEdge:
        edge = await self.repo.create_edge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, properties=properties or {},
            tenant_id=tenant_id,
        )
        self.metrics.edges_created += 1
        return edge

    # ── Graph Population ────────────────────────────────────────

    async def populate_from_golden_record(self, golden_record: dict, tenant_id: str) -> dict:
        t0 = time.monotonic()
        stats = {"nodes": 0, "edges": 0}

        company_node = await self.upsert_company(golden_record, tenant_id)
        stats["nodes"] += 1

        company_id = golden_record.get("company_id") or golden_record.get("id")
        if not company_id:
            return stats

        if not (tenant_id or "").strip():
            raise ValueError("tenant_id is required for populate_from_golden_record")

        async with self._session_factory() as session:
            # licenses/branches have no tenant_id column — scope via companies join
            rows = await session.execute(
                sa_text(
                    "SELECT l.* FROM licenses l "
                    "JOIN companies c ON c.id = l.company_id "
                    "WHERE l.company_id = :cid AND c.tenant_id = :tid"
                ),
                {"cid": company_id, "tid": tenant_id},
            )
            for lic in rows.mappings().all():
                lic_node = await self.repo.upsert_license(dict(lic), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, lic_node.id, EdgeType.HAS_LICENSE, tenant_id=tenant_id)
                stats["edges"] += 1

            rows = await session.execute(
                sa_text(
                    "SELECT b.* FROM branches b "
                    "JOIN companies c ON c.id = b.company_id "
                    "WHERE b.company_id = :cid AND c.tenant_id = :tid"
                ),
                {"cid": company_id, "tid": tenant_id},
            )
            for branch in rows.mappings().all():
                branch_node = await self.repo.upsert_branch(dict(branch), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, branch_node.id, EdgeType.HAS_BRANCH, tenant_id=tenant_id)
                stats["edges"] += 1

            rows = await session.execute(
                sa_text("SELECT * FROM contacts WHERE company_id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            for contact in rows.mappings().all():
                person_node = await self.upsert_person(dict(contact), tenant_id)
                stats["nodes"] += 1
                await self.create_edge(company_node.id, person_node.id, EdgeType.EMPLOYS, tenant_id=tenant_id)
                stats["edges"] += 1

        inferred = await self._infer_relationships(company_id, tenant_id)
        stats["edges"] += inferred

        self.metrics.sync_count += 1
        elapsed = (time.monotonic() - t0) * 1000
        if self._logger:
            self._logger.info("Graph populated for company %s: %s (%.0fms)", company_id, stats, elapsed)

        return stats

    # ── Graph Queries ───────────────────────────────────────────

    async def find_competitors(self, company_id: str, tenant_id: str, limit: int = 10) -> list[GraphNode]:
        return await self.repo.find_competitors(company_id=company_id, tenant_id=tenant_id, limit=limit)

    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 6, tenant_id: str = ""
    ) -> Optional[GraphPath]:
        return await self.repo.find_path(source_id=source_id, target_id=target_id, max_depth=max_depth, tenant_id=tenant_id)

    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        return await self.repo.get_ego_network(company_id=company_id, depth=depth, tenant_id=tenant_id)

    async def get_decision_makers(self, company_id: str, tenant_id: str = "") -> list[GraphNode]:
        return await self.repo.get_decision_makers(company_id=company_id, tenant_id=tenant_id)

    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        return await self.repo.search(query=query, labels=labels, limit=limit, tenant_id=tenant_id)

    # ── Relationship Enrichment ─────────────────────────────────

    async def enrich_company_relationships(self, company_id: str, tenant_id: str) -> dict:
        return await self._enrich_company_relationships_impl(company_id, tenant_id)

    async def get_entity_subgraph(self, entity_id: str, depth: int = 2, tenant_id: str = "") -> dict:
        return await self.repo.get_entity_subgraph(entity_id=entity_id, depth=depth, tenant_id=tenant_id)

    async def merge_graph_nodes(
        self, surviving_id: str, absorbed_id: str, tenant_id: str = ""
    ) -> dict:
        result = await self.repo.merge_graph_nodes(surviving_id=surviving_id, absorbed_id=absorbed_id, tenant_id=tenant_id)
        if result.get("node_deleted"):
            self.metrics.nodes_created -= 1
        return result

    # ── Maintenance ─────────────────────────────────────────────

    async def rebuild(self, tenant_id: str) -> dict:
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

    # ── Company Insights ────────────────────────────────────────

    async def get_company_insights(self, company_id: str, tenant_id: str) -> dict:
        competitors_direct: list[dict] = []
        competitors_indirect: list[dict] = []
        partners: list[dict] = []
        subsidiaries: list[dict] = []
        parent: dict | None = None
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("SELECT id, name_ar, name_en, industry, city, region, employees_count, capital, legal_form FROM companies WHERE id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            company = row.mappings().one_or_none()
            if not company:
                return {"error": "Company not found"}
            industry = company.get("industry") or ""
            city = company.get("city") or ""
            region = company.get("region") or ""
            edges = await session.execute(
                sa_text(
                    "SELECT ge.source_id, ge.target_id, c.name_ar, c.name_en, c.industry, c.city "
                    "FROM graph_edges ge "
                    "JOIN companies c ON (c.id::text = ge.target_id OR c.id::text = ge.source_id) "
                    "WHERE (ge.source_id = :cid OR ge.target_id = :cid) "
                    "AND ge.edge_type = 'COMPETITOR_OF' AND c.id::text != :cid AND c.tenant_id = :tid"
                ),
                {"cid": company_id, "tid": tenant_id},
            )
            for edge in edges.mappings().all():
                comp_id = edge["target_id"] if edge["source_id"] == company_id else edge["source_id"]
                competitors_direct.append({"id": comp_id, "name_ar": edge.get("name_ar"), "name_en": edge.get("name_en"), "industry": edge.get("industry"), "city": edge.get("city")})
            if industry or city:
                conditions, params = [], {"cid": company_id, "tid": tenant_id}
                if industry:
                    conditions.append("c.industry = :industry")
                    params["industry"] = industry
                if city:
                    conditions.append("c.city = :city")
                    params["city"] = city
                existing = {c["id"] for c in competitors_direct}
                indirect_rows = await session.execute(
                    sa_text(f"SELECT id, name_ar, name_en, industry, city FROM companies c WHERE c.id != :cid AND c.tenant_id = :tid AND ({' OR '.join(conditions)}) LIMIT 20"),
                    params,
                )
                for r in indirect_rows.mappings().all():
                    if r["id"] not in existing:
                        competitors_indirect.append({"id": r["id"], "name_ar": r.get("name_ar"), "name_en": r.get("name_en"), "industry": r.get("industry"), "city": r.get("city")})
            partner_edges = await session.execute(
                sa_text(
                    "SELECT ge.source_id, ge.target_id, ge.properties, c.name_ar, c.name_en, c.industry, c.city "
                    "FROM graph_edges ge "
                    "JOIN companies c ON (c.id::text = ge.target_id OR c.id::text = ge.source_id) "
                    "WHERE (ge.source_id = :cid OR ge.target_id = :cid) "
                    "AND ge.edge_type = 'PARTNER_WITH' AND c.id::text != :cid AND c.tenant_id = :tid"
                ),
                {"cid": company_id, "tid": tenant_id},
            )
            for edge in partner_edges.mappings().all():
                pid = edge["target_id"] if edge["source_id"] == company_id else edge["source_id"]
                partners.append({"id": pid, "name_ar": edge.get("name_ar"), "name_en": edge.get("name_en"), "industry": edge.get("industry"), "city": edge.get("city"), "reason": edge.get("properties", {}).get("reason")})
            parent_row = await session.execute(sa_text("SELECT id, name_ar, name_en FROM companies WHERE id = (SELECT parent_company_id FROM companies WHERE id = :cid)"), {"cid": company_id})
            p = parent_row.mappings().one_or_none()
            if p:
                parent = {"id": str(p["id"]), "name_ar": p.get("name_ar"), "name_en": p.get("name_en")}
            sub_rows = await session.execute(sa_text("SELECT id, name_ar, name_en, industry, city FROM companies WHERE parent_company_id = :cid AND tenant_id = :tid"), {"cid": company_id, "tid": tenant_id})
            subsidiaries = [{"id": str(r["id"]), "name_ar": r.get("name_ar"), "name_en": r.get("name_en"), "industry": r.get("industry"), "city": r.get("city")} for r in sub_rows.mappings().all()]
            total_same_industry = 0
            if industry:
                cnt = await session.scalar(sa_text("SELECT COUNT(*) FROM companies WHERE tenant_id = :tid AND industry = :industry AND is_active = true"), {"tid": tenant_id, "industry": industry})
                total_same_industry = cnt or 0
            cmp_count = len(competitors_direct)
            ptn_count = len(partners)
        return {
            "company_id": company_id,
            "competitors": {"direct": competitors_direct, "indirect": competitors_indirect},
            "partners": partners,
            "hierarchy": {"parent": parent, "subsidiaries": subsidiaries},
            "market_position": {"industry": industry, "city": city, "region": region, "employees_count": company.get("employees_count"), "capital": company.get("capital"), "legal_form": company.get("legal_form"), "total_competitors": cmp_count + len(competitors_indirect), "direct_competitors": cmp_count, "indirect_competitors": len(competitors_indirect), "total_partners": ptn_count, "total_subsidiaries": len(subsidiaries), "has_parent": parent is not None, "total_companies_in_industry": total_same_industry},
            "relationship_strength_scores": {"competitive_intensity": min(1.0, cmp_count / 20.0), "partnership_density": min(1.0, ptn_count / 10.0), "hierarchy_depth": 1 if subsidiaries else (2 if parent else 0), "network_reach": min(1.0, (cmp_count + ptn_count + len(subsidiaries)) / 30.0)},
        }

    # ── Relationship inference (internal) ───────────────────────

    async def _infer_relationships(self, company_id: str, tenant_id: str) -> int:
        count = 0
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("SELECT industry, city FROM companies WHERE id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            company = row.mappings().one_or_none()
            if not company:
                return 0

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
                    await self.create_edge(company_id, comp["id"], EdgeType.COMPETITOR_OF, tenant_id=tenant_id)
                    count += 1

            subs = await session.execute(
                sa_text("SELECT id FROM companies WHERE parent_company_id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            for sub in subs.mappings().all():
                await self.create_edge(company_id, sub["id"], EdgeType.SUBSIDIARY_OF, tenant_id=tenant_id)
                count += 1

        return count

    async def _enrich_company_relationships_impl(self, company_id: str, tenant_id: str) -> dict:
        stats = {"competitors": 0, "partners": 0, "subsidiaries": 0}
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("SELECT industry, city FROM companies WHERE id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            company = row.mappings().one_or_none()
            if not company:
                return stats

            industry = company.get("industry") or ""
            city = company.get("city") or ""

            if industry or city:
                conditions = []
                params: dict = {"cid": company_id, "tid": tenant_id}
                if industry:
                    conditions.append("c.industry = :industry")
                    params["industry"] = industry
                if city:
                    conditions.append("c.city = :city")
                    params["city"] = city
                where = " OR ".join(conditions)
                comp_rows = await session.execute(
                    sa_text(f"SELECT id, industry, city FROM companies c WHERE c.id != :cid AND c.tenant_id = :tid AND ({where}) LIMIT 30"),
                    params,
                )
                for comp in comp_rows.mappings().all():
                    reason = "same_industry" if comp.get("industry") == industry else "same_city"
                    await self.create_edge(
                        company_id, comp["id"], EdgeType.COMPETITOR_OF, {"reason": reason}, tenant_id=tenant_id
                    )
                    stats["competitors"] += 1

            sub_rows = await session.execute(
                sa_text("SELECT id FROM companies WHERE parent_company_id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            for sub in sub_rows.mappings().all():
                await self.create_edge(company_id, sub["id"], EdgeType.SUBSIDIARY_OF, tenant_id=tenant_id)
                stats["subsidiaries"] += 1

            if city:
                partner_rows = await session.execute(
                    sa_text("SELECT id, industry FROM companies c WHERE c.id != :cid AND c.tenant_id = :tid AND c.city = :city AND c.industry != :industry AND c.industry IS NOT NULL AND c.industry != '' LIMIT 15"),
                    {"cid": company_id, "tid": tenant_id, "city": city, "industry": industry},
                )
                for partner in partner_rows.mappings().all():
                    await self.create_edge(
                        company_id,
                        partner["id"],
                        EdgeType.PARTNER_WITH,
                        {"reason": "same_city_different_industry"},
                        tenant_id=tenant_id,
                    )
                    stats["partners"] += 1
        return stats
