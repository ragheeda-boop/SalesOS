"""SQL-backed graph repository implementation (fallback store)."""

from __future__ import annotations

from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EdgeType, GraphEdge, GraphNode, GraphPath, NodeLabel
from .base import GraphRepository


class SqlGraphRepository(GraphRepository):
    """Graph repository backed by PostgreSQL via SQLAlchemy async sessions."""

    def __init__(self, session_factory: Callable[[], AsyncSession], logger: Any = None):
        self._session_factory = session_factory
        self._logger = logger

    # ── Node operations ─────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str = "") -> GraphNode:
        cid = company.get("company_id") or company.get("id") or company.get("cr_number", "")
        return GraphNode(id=cid, labels=[NodeLabel.COMPANY], properties=company)

    async def upsert_person(self, person: dict, tenant_id: str = "") -> GraphNode:
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
        props = {**(properties or {}), "tenant_id": tenant_id} if tenant_id else (properties or {})
        async with self._session_factory() as session:
            await session.execute(
                sa_text(
                    "INSERT INTO graph_edges (source_id, target_id, edge_type, properties) "
                    "VALUES (:src, :tgt, :type, :props) "
                    "ON CONFLICT (source_id, target_id, edge_type) DO NOTHING"
                ),
                {"src": source_id, "tgt": target_id, "type": edge_type.value, "props": props},
            )
            await session.commit()
        return GraphEdge(source_id=source_id, target_id=target_id, type=edge_type, properties=props)

    async def get_node(
        self,
        node_id: str,
        labels: Optional[list[NodeLabel]] = None,
        tenant_id: str = "",
    ) -> Optional[GraphNode]:
        async with self._session_factory() as session:
            if tenant_id:
                row = await session.execute(
                    sa_text("SELECT * FROM companies WHERE id = :id AND tenant_id = :tid"),
                    {"id": node_id, "tid": tenant_id},
                )
            else:
                row = await session.execute(sa_text("SELECT * FROM companies WHERE id = :id"), {"id": node_id})
            r = row.mappings().one_or_none()
            return GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r)) if r else None

    # ── Graph traversal ─────────────────────────────────────────

    async def find_competitors(
        self, company_id: str, tenant_id: str = "", limit: int = 10
    ) -> list[GraphNode]:
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text(
                    """
                    SELECT ge.*
                    FROM graph_edges ge
                    JOIN companies c_src ON c_src.id::text = ge.source_id
                    JOIN companies c_tgt ON c_tgt.id::text = ge.target_id
                    WHERE (ge.source_id = :cid OR ge.target_id = :cid)
                      AND ge.edge_type = 'COMPETITOR_OF'
                      AND c_src.tenant_id = :tid
                      AND c_tgt.tenant_id = :tid
                    LIMIT :lim
                    """
                ),
                {"cid": company_id, "tid": tenant_id, "lim": limit},
            )
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
        async with self._session_factory() as session:
            if tenant_id:
                row = await session.execute(
                    sa_text(
                        """
                        SELECT ge.*
                        FROM graph_edges ge
                        JOIN companies c_src ON c_src.id::text = ge.source_id AND c_src.tenant_id = :tid
                        JOIN companies c_tgt ON c_tgt.id::text = ge.target_id AND c_tgt.tenant_id = :tid
                        WHERE (ge.source_id = :src AND ge.target_id = :tgt)
                           OR (ge.source_id = :tgt AND ge.target_id = :src)
                        LIMIT 1
                        """
                    ),
                    {"src": source_id, "tgt": target_id, "tid": tenant_id},
                )
            else:
                row = await session.execute(
                    sa_text(
                        "SELECT * FROM graph_edges WHERE (source_id = :src AND target_id = :tgt) "
                        "OR (source_id = :tgt AND target_id = :src) LIMIT 1"
                    ),
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
                edges=[GraphEdge(source_id=edge["source_id"], target_id=edge["target_id"], type=EdgeType(edge["edge_type"]))],
                length=1,
            )

    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        async with self._session_factory() as session:
            if tenant_id:
                rows = await session.execute(
                    sa_text(
                        """
                        SELECT ge.*
                        FROM graph_edges ge
                        JOIN companies c_src ON c_src.id::text = ge.source_id AND c_src.tenant_id = :tid
                        JOIN companies c_tgt ON c_tgt.id::text = ge.target_id AND c_tgt.tenant_id = :tid
                        WHERE ge.source_id = :cid OR ge.target_id = :cid
                        LIMIT 50
                        """
                    ),
                    {"cid": company_id, "tid": tenant_id},
                )
            else:
                rows = await session.execute(
                    sa_text("SELECT * FROM graph_edges WHERE source_id = :cid OR target_id = :cid LIMIT 50"),
                    {"cid": company_id},
                )
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
        async with self._session_factory() as session:
            if tenant_id:
                rows = await session.execute(
                    sa_text(
                        """
                        SELECT * FROM contacts
                        WHERE company_id = :cid AND tenant_id = :tid
                          AND (position ILIKE '%CEO%' OR position ILIKE '%CTO%' OR position ILIKE '%VP%'
                               OR position ILIKE '%Director%' OR position ILIKE '%Head%'
                               OR position ILIKE '%President%')
                        """
                    ),
                    {"cid": company_id, "tid": tenant_id},
                )
            else:
                rows = await session.execute(
                    sa_text(
                        "SELECT * FROM contacts WHERE company_id = :cid AND "
                        "(position ILIKE '%CEO%' OR position ILIKE '%CTO%' OR position ILIKE '%VP%' "
                        "OR position ILIKE '%Director%' OR position ILIKE '%Head%' OR position ILIKE '%President%')"
                    ),
                    {"cid": company_id},
                )
            return [GraphNode(id=r["id"], labels=[NodeLabel.PERSON], properties=dict(r)) for r in rows.mappings().all()]

    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        async with self._session_factory() as session:
            if tenant_id:
                rows = await session.execute(
                    sa_text(
                        """
                        SELECT id, name_ar, name_en, cr_number, industry, city
                        FROM companies
                        WHERE tenant_id = :tid
                          AND (name_ar ILIKE :q OR name_en ILIKE :q OR cr_number ILIKE :q)
                        LIMIT :lim
                        """
                    ),
                    {"q": f"%{query}%", "lim": limit, "tid": tenant_id},
                )
            else:
                rows = await session.execute(
                    sa_text(
                        "SELECT id, name_ar, name_en, cr_number, industry, city FROM companies "
                        "WHERE name_ar ILIKE :q OR name_en ILIKE :q OR cr_number ILIKE :q LIMIT :lim"
                    ),
                    {"q": f"%{query}%", "lim": limit},
                )
            return [GraphNode(id=r["id"], labels=[NodeLabel.COMPANY], properties=dict(r)) for r in rows.mappings().all()]

    # ── Entity operations ───────────────────────────────────────

    async def upsert_license(self, lic: dict, tenant_id: str = "") -> GraphNode:
        lid = lic.get("id") or lic.get("license_number", "")
        return GraphNode(id=lid, labels=[NodeLabel.LICENSE], properties=lic)

    async def upsert_branch(self, branch: dict, tenant_id: str = "") -> GraphNode:
        bid = branch.get("id", "")
        return GraphNode(id=bid, labels=[NodeLabel.BRANCH], properties=branch)

    async def get_entity_subgraph(
        self, entity_id: str, depth: int = 2, tenant_id: str = ""
    ) -> dict:
        async with self._session_factory() as session:
            if tenant_id:
                rows = await session.execute(
                    sa_text(
                        """
                        SELECT ge.*
                        FROM graph_edges ge
                        JOIN companies c_src ON c_src.id::text = ge.source_id AND c_src.tenant_id = :tid
                        JOIN companies c_tgt ON c_tgt.id::text = ge.target_id AND c_tgt.tenant_id = :tid
                        WHERE ge.source_id = :eid OR ge.target_id = :eid
                        LIMIT :lim
                        """
                    ),
                    {"eid": entity_id, "tid": tenant_id, "lim": 50 * depth},
                )
            else:
                rows = await session.execute(
                    sa_text(
                        "SELECT * FROM graph_edges WHERE (source_id = :eid OR target_id = :eid) LIMIT :lim"
                    ),
                    {"eid": entity_id, "lim": 50 * depth},
                )
            nodes: dict[str, dict] = {}
            edges: list[dict] = []
            for row in rows.mappings().all():
                src, tgt = row["source_id"], row["target_id"]
                if src not in nodes:
                    nodes[src] = GraphNode(id=src, labels=[NodeLabel.COMPANY], properties={}).to_dict()
                if tgt not in nodes:
                    nodes[tgt] = GraphNode(id=tgt, labels=[NodeLabel.COMPANY], properties={}).to_dict()
                edges.append({"source": src, "target": tgt, "type": row["edge_type"]})
            return {"nodes": list(nodes.values()), "edges": edges}

    async def merge_graph_nodes(
        self, surviving_id: str, absorbed_id: str, tenant_id: str = ""
    ) -> dict:
        async with self._session_factory() as session:
            if tenant_id:
                owned = await session.execute(
                    sa_text(
                        "SELECT COUNT(*) FROM companies WHERE id IN (:surviving, :absorbed) AND tenant_id = :tid"
                    ),
                    {"surviving": surviving_id, "absorbed": absorbed_id, "tid": tenant_id},
                )
                if (owned.scalar() or 0) < 2:
                    return {"edges_rewired": 0, "node_deleted": False, "error": "tenant_mismatch"}
            await session.execute(
                sa_text(
                    "UPDATE graph_edges SET source_id = :surviving WHERE source_id = :absorbed "
                    "AND NOT EXISTS (SELECT 1 FROM graph_edges e2 WHERE e2.source_id = :surviving "
                    "AND e2.target_id = graph_edges.target_id)"
                ),
                {"surviving": surviving_id, "absorbed": absorbed_id},
            )
            await session.execute(
                sa_text(
                    "UPDATE graph_edges SET target_id = :surviving WHERE target_id = :absorbed "
                    "AND NOT EXISTS (SELECT 1 FROM graph_edges e2 WHERE e2.source_id = graph_edges.source_id "
                    "AND e2.target_id = :surviving)"
                ),
                {"surviving": surviving_id, "absorbed": absorbed_id},
            )
            result = await session.execute(
                sa_text("DELETE FROM graph_edges WHERE source_id = :absorbed OR target_id = :absorbed"),
                {"absorbed": absorbed_id},
            )
            await session.commit()
        return {"edges_rewired": result.rowcount if result.rowcount else 0, "node_deleted": True}
