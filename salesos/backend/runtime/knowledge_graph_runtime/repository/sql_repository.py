"""SQL-backed graph repository implementation (fallback store).

CI-19 Wave 2 Core (no sqlalchemy.text)

All query paths require a non-empty tenant_id — unscoped SQL is refused.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    cast,
    delete,
    exists,
    func,
    literal,
    or_,
    select,
    type_coerce,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EdgeType, GraphEdge, GraphNode, GraphPath, NodeLabel
from .base import GraphRepository

_kg_metadata = MetaData()

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]

companies = Table(
    "companies",
    _kg_metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", PGUUID(as_uuid=True)),
    Column("name_ar", String),
    Column("name_en", String),
    Column("cr_number", String),
    Column("industry", String),
    Column("city", String),
    Column("region", String),
    Column("employees_count", Integer),
    Column("capital", String),
    Column("legal_form", String),
    Column("is_active", Boolean),
    # Note: companies.parent_company_id is not in the migrated schema; hierarchy
    # is modeled via graph_edges (SUBSIDIARY_OF), not a companies FK column.
)

contacts = Table(
    "contacts",
    _kg_metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", PGUUID(as_uuid=True)),
    Column("company_id", PGUUID(as_uuid=True)),
    Column("position", String),
)

licenses = Table(
    "licenses",
    _kg_metadata,
    Column("id", String(64), primary_key=True),
    Column("company_id", PGUUID(as_uuid=True)),
)

branches = Table(
    "branches",
    _kg_metadata,
    Column("id", String(64), primary_key=True),
    Column("company_id", PGUUID(as_uuid=True)),
)

graph_edges = Table(
    "graph_edges",
    _kg_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", String(64), nullable=False),
    Column("target_id", String(64), nullable=False),
    Column("edge_type", String(50), nullable=False),
    Column("properties", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    # Live indexes — metadata register only (DEC-130d); do not DROP
    Index("ix_graph_edges_source", "source_id", "edge_type"),
    Index("ix_graph_edges_target", "target_id", "edge_type"),
    Index("ix_graph_edges_unique", "source_id", "target_id", "edge_type", unique=True),
)

golden_records = Table(
    "golden_records",
    _kg_metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", PGUUID(as_uuid=True)),
    Column("is_active", Boolean),
)


def _id_text(col):
    return cast(col, String)


class SqlGraphRepository(GraphRepository):
    """Graph repository backed by PostgreSQL via SQLAlchemy async sessions."""

    def __init__(self, session_factory: SessionFactory, logger: Any = None):
        self._session_factory = session_factory
        self._logger = logger

    @staticmethod
    def _require_tenant(tenant_id: str) -> str:
        tid = (tenant_id or "").strip()
        if not tid:
            raise ValueError("tenant_id is required for SQL graph queries")
        return tid

    # ── Node operations ─────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str = "") -> GraphNode:
        self._require_tenant(tenant_id)
        cid = company.get("company_id") or company.get("id") or company.get("cr_number", "")
        return GraphNode(id=cid, labels=[NodeLabel.COMPANY], properties=company)

    async def upsert_person(self, person: dict, tenant_id: str = "") -> GraphNode:
        self._require_tenant(tenant_id)
        pid = person.get("id") or person.get("email", "")
        return GraphNode(id=pid, labels=[NodeLabel.PERSON], properties=person)

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: dict,
        tenant_id: str = "",
    ) -> GraphEdge:
        tid = self._require_tenant(tenant_id)
        props = {**(properties or {}), "tenant_id": tid}
        stmt = (
            pg_insert(graph_edges)
            .values(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type.value,
                # asyncpg needs an explicit JSONB bind (plain dict → encode error).
                properties=type_coerce(props, JSONB),
            )
            .on_conflict_do_nothing(
                index_elements=[
                    graph_edges.c.source_id,
                    graph_edges.c.target_id,
                    graph_edges.c.edge_type,
                ]
            )
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()
        return GraphEdge(source_id=source_id, target_id=target_id, type=edge_type, properties=props)

    async def get_node(
        self,
        node_id: str,
        labels: Optional[list[NodeLabel]] = None,
        tenant_id: str = "",
    ) -> Optional[GraphNode]:
        tid = self._require_tenant(tenant_id)
        stmt = select(companies).where(
            companies.c.id == node_id,
            companies.c.tenant_id == tid,
        )
        async with self._session_factory() as session:
            row = await session.execute(stmt)
            r = row.mappings().one_or_none()
            return GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r)) if r else None

    # ── Graph traversal ─────────────────────────────────────────

    async def find_competitors(
        self, company_id: str, tenant_id: str = "", limit: int = 10
    ) -> list[GraphNode]:
        tid = self._require_tenant(tenant_id)
        c_src = companies.alias("c_src")
        c_tgt = companies.alias("c_tgt")
        stmt = (
            select(graph_edges)
            .select_from(
                graph_edges.join(
                    c_src, _id_text(c_src.c.id) == graph_edges.c.source_id
                ).join(c_tgt, _id_text(c_tgt.c.id) == graph_edges.c.target_id)
            )
            .where(
                or_(
                    graph_edges.c.source_id == company_id,
                    graph_edges.c.target_id == company_id,
                ),
                graph_edges.c.edge_type == "COMPETITOR_OF",
                c_src.c.tenant_id == tid,
                c_tgt.c.tenant_id == tid,
            )
            .limit(limit)
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            return [
                GraphNode(
                    id=(r["target_id"] if r["source_id"] == company_id else r["source_id"]),
                    labels=[NodeLabel.COMPANY],
                    properties={},
                )
                for r in rows.mappings().all()
            ]

    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 6, tenant_id: str = ""
    ) -> Optional[GraphPath]:
        tid = self._require_tenant(tenant_id)
        c_src = companies.alias("c_src")
        c_tgt = companies.alias("c_tgt")
        stmt = (
            select(graph_edges)
            .select_from(
                graph_edges.join(
                    c_src,
                    (_id_text(c_src.c.id) == graph_edges.c.source_id)
                    & (c_src.c.tenant_id == tid),
                ).join(
                    c_tgt,
                    (_id_text(c_tgt.c.id) == graph_edges.c.target_id)
                    & (c_tgt.c.tenant_id == tid),
                )
            )
            .where(
                or_(
                    (graph_edges.c.source_id == source_id)
                    & (graph_edges.c.target_id == target_id),
                    (graph_edges.c.source_id == target_id)
                    & (graph_edges.c.target_id == source_id),
                )
            )
            .limit(1)
        )
        async with self._session_factory() as session:
            row = await session.execute(stmt)
            edge = row.mappings().one_or_none()
            if not edge:
                return None
            return GraphPath(
                nodes=[
                    GraphNode(id=source_id, labels=[NodeLabel.COMPANY], properties={}),
                    GraphNode(id=target_id, labels=[NodeLabel.COMPANY], properties={}),
                ],
                edges=[
                    GraphEdge(
                        source_id=edge["source_id"],
                        target_id=edge["target_id"],
                        type=EdgeType(edge["edge_type"]),
                    )
                ],
                length=1,
            )

    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        tid = self._require_tenant(tenant_id)
        c_src = companies.alias("c_src")
        c_tgt = companies.alias("c_tgt")
        stmt = (
            select(graph_edges)
            .select_from(
                graph_edges.join(
                    c_src,
                    (_id_text(c_src.c.id) == graph_edges.c.source_id)
                    & (c_src.c.tenant_id == tid),
                ).join(
                    c_tgt,
                    (_id_text(c_tgt.c.id) == graph_edges.c.target_id)
                    & (c_tgt.c.tenant_id == tid),
                )
            )
            .where(
                or_(
                    graph_edges.c.source_id == company_id,
                    graph_edges.c.target_id == company_id,
                )
            )
            .limit(50)
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            return [
                {
                    "node": GraphNode(
                        id=(r["target_id"] if r["source_id"] == company_id else r["source_id"]),
                        labels=[NodeLabel.COMPANY],
                        properties={},
                    ).to_dict(),
                    "relationship": r["edge_type"],
                }
                for r in rows.mappings().all()
            ]

    async def get_decision_makers(
        self, company_id: str, tenant_id: str = ""
    ) -> list[GraphNode]:
        tid = self._require_tenant(tenant_id)
        position = contacts.c.position
        stmt = select(contacts).where(
            contacts.c.company_id == company_id,
            contacts.c.tenant_id == tid,
            or_(
                position.ilike("%CEO%"),
                position.ilike("%CTO%"),
                position.ilike("%VP%"),
                position.ilike("%Director%"),
                position.ilike("%Head%"),
                position.ilike("%President%"),
            ),
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            return [
                GraphNode(id=r["id"], labels=[NodeLabel.PERSON], properties=dict(r))
                for r in rows.mappings().all()
            ]

    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        tid = self._require_tenant(tenant_id)
        pattern = f"%{query}%"
        stmt = (
            select(
                companies.c.id,
                companies.c.name_ar,
                companies.c.name_en,
                companies.c.cr_number,
                companies.c.industry,
                companies.c.city,
            )
            .where(
                companies.c.tenant_id == tid,
                or_(
                    companies.c.name_ar.ilike(pattern),
                    companies.c.name_en.ilike(pattern),
                    companies.c.cr_number.ilike(pattern),
                ),
            )
            .limit(limit)
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            return [
                GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r))
                for r in rows.mappings().all()
            ]

    # ── Entity operations ───────────────────────────────────────

    async def upsert_license(self, lic: dict, tenant_id: str = "") -> GraphNode:
        self._require_tenant(tenant_id)
        lid = lic.get("id") or lic.get("license_number", "")
        return GraphNode(id=lid, labels=[NodeLabel.LICENSE], properties=lic)

    async def upsert_branch(self, branch: dict, tenant_id: str = "") -> GraphNode:
        self._require_tenant(tenant_id)
        bid = branch.get("id", "")
        return GraphNode(id=bid, labels=[NodeLabel.BRANCH], properties=branch)

    async def get_entity_subgraph(
        self, entity_id: str, depth: int = 2, tenant_id: str = ""
    ) -> dict:
        tid = self._require_tenant(tenant_id)
        c_src = companies.alias("c_src")
        c_tgt = companies.alias("c_tgt")
        stmt = (
            select(graph_edges)
            .select_from(
                graph_edges.join(
                    c_src,
                    (_id_text(c_src.c.id) == graph_edges.c.source_id)
                    & (c_src.c.tenant_id == tid),
                ).join(
                    c_tgt,
                    (_id_text(c_tgt.c.id) == graph_edges.c.target_id)
                    & (c_tgt.c.tenant_id == tid),
                )
            )
            .where(
                or_(
                    graph_edges.c.source_id == entity_id,
                    graph_edges.c.target_id == entity_id,
                )
            )
            .limit(50 * depth)
        )
        async with self._session_factory() as session:
            rows = await session.execute(stmt)
            nodes: dict[str, dict] = {}
            edges: list[dict] = []
            for row in rows.mappings().all():
                src, tgt = row["source_id"], row["target_id"]
                if src not in nodes:
                    nodes[src] = GraphNode(
                        id=src, labels=[NodeLabel.COMPANY], properties={}
                    ).to_dict()
                if tgt not in nodes:
                    nodes[tgt] = GraphNode(
                        id=tgt, labels=[NodeLabel.COMPANY], properties={}
                    ).to_dict()
                edges.append({"source": src, "target": tgt, "type": row["edge_type"]})
            return {"nodes": list(nodes.values()), "edges": edges}

    async def merge_graph_nodes(
        self, surviving_id: str, absorbed_id: str, tenant_id: str = ""
    ) -> dict:
        tid = self._require_tenant(tenant_id)
        async with self._session_factory() as session:
            owned = await session.scalar(
                select(func.count())
                .select_from(companies)
                .where(
                    companies.c.id.in_([surviving_id, absorbed_id]),
                    companies.c.tenant_id == tid,
                )
            )
            if (owned or 0) < 2:
                return {"edges_rewired": 0, "node_deleted": False, "error": "tenant_mismatch"}

            e2 = graph_edges.alias("e2")
            await session.execute(
                update(graph_edges)
                .where(
                    graph_edges.c.source_id == absorbed_id,
                    ~exists(
                        select(literal(1)).where(
                            e2.c.source_id == surviving_id,
                            e2.c.target_id == graph_edges.c.target_id,
                        )
                    ),
                )
                .values(source_id=surviving_id)
            )
            await session.execute(
                update(graph_edges)
                .where(
                    graph_edges.c.target_id == absorbed_id,
                    ~exists(
                        select(literal(1)).where(
                            e2.c.source_id == graph_edges.c.source_id,
                            e2.c.target_id == surviving_id,
                        )
                    ),
                )
                .values(target_id=surviving_id)
            )
            result = await session.execute(
                delete(graph_edges).where(
                    or_(
                        graph_edges.c.source_id == absorbed_id,
                        graph_edges.c.target_id == absorbed_id,
                    )
                )
            )
            await session.commit()
        return {
            "edges_rewired": result.rowcount if result.rowcount else 0,
            "node_deleted": True,
        }
