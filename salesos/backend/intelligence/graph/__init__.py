from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import EntityType
from ..company import CompanyIntelligenceEngine


@dataclass
class Relationship:
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None


@dataclass
class GraphNode:
    id: str
    entity_type: EntityType
    name: str
    relationships: list[Relationship] = field(default_factory=list)

    @property
    def degree(self) -> int:
        return len(self.relationships)


@dataclass
class GraphPath:
    nodes: list[GraphNode]
    edges: list[Relationship]
    total_strength: float
    length: int


class RelationshipGraphService:
    """
    Manages the network of relationships between business objects.
    Companies ↔ People ↔ Suppliers ↔ Customers ↔ Projects
    """

    def __init__(self, company_engine: Optional[CompanyIntelligenceEngine] = None):
        self.company_engine = company_engine
        self._nodes: dict[str, GraphNode] = {}
        self._relationships: list[Relationship] = []

    def add_node(self, node_id: str, entity_type: EntityType, name: str) -> GraphNode:
        existing = self._nodes.get(node_id)
        if existing:
            return existing
        node = GraphNode(id=node_id, entity_type=entity_type, name=name)
        self._nodes[node_id] = node
        return node

    def add_relationship(self, source_id: str, target_id: str,
                         rel_type: str, strength: float = 0.5,
                         metadata: Optional[dict[str, Any]] = None) -> Relationship:
        source = self._nodes.get(source_id)
        target = self._nodes.get(target_id)
        if not source or not target:
            raise ValueError(f"Cannot create relationship: node(s) not found ({source_id}, {target_id})")

        rel = Relationship(
            source_id=source_id, target_id=target_id,
            relationship_type=rel_type, strength=strength,
            metadata=metadata or {},
        )
        self._relationships.append(rel)
        source.relationships.append(rel)
        return rel

    def add_bidirectional(self, id_a: str, id_b: str, rel_type: str,
                          strength: float = 0.5) -> tuple[Relationship, Relationship]:
        return (
            self.add_relationship(id_a, id_b, rel_type, strength),
            self.add_relationship(id_b, id_a, f"{rel_type}_reverse", strength * 0.8),
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_relationships(self, node_id: str,
                          rel_type: Optional[str] = None) -> list[Relationship]:
        node = self._nodes.get(node_id)
        if not node:
            return []
        if rel_type:
            return [r for r in node.relationships if r.relationship_type == rel_type]
        return node.relationships

    def find_path(self, source_id: str, target_id: str, max_depth: int = 3) -> Optional[GraphPath]:
        """BFS to find shortest path between two nodes."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        visited = {source_id}
        queue: list[list[str]] = [[source_id]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == target_id:
                nodes = [self._nodes[nid] for nid in path]
                edges = []
                total_strength = 0.0
                for i in range(len(path) - 1):
                    for rel in self._nodes[path[i]].relationships:
                        if rel.target_id == path[i + 1]:
                            edges.append(rel)
                            total_strength += rel.strength
                            break
                return GraphPath(
                    nodes=nodes, edges=edges,
                    total_strength=round(total_strength, 2),
                    length=len(path) - 1,
                )

            if len(path) >= max_depth:
                continue

            for rel in self._nodes[current].relationships:
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append(path + [rel.target_id])

        return None

    def get_connected_companies(self, company_id: str,
                                max_degree: int = 2) -> list[GraphNode]:
        """Find all companies connected to this one."""
        connected = []
        visited = {company_id}
        queue = [(company_id, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_degree:
                continue

            for rel in self._nodes[current].relationships:
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    target = self._nodes.get(rel.target_id)
                    if target:
                        connected.append(target)
                        queue.append((rel.target_id, depth + 1))

        return connected

    def suggest_connections(self, node_id: str, rel_type: Optional[str] = None) -> list[dict[str, Any]]:
        """Suggest potential connections based on shared relationships."""
        node = self._nodes.get(node_id)
        if not node:
            return []

        connected_ids = {r.target_id for r in node.relationships}
        suggestions: dict[str, float] = {}

        for rel in node.relationships:
            neighbor = self._nodes.get(rel.target_id)
            if not neighbor:
                continue
            for neighbor_rel in neighbor.relationships:
                if neighbor_rel.target_id not in connected_ids and neighbor_rel.target_id != node_id:
                    if rel_type and neighbor_rel.relationship_type != rel_type:
                        continue
                    current = suggestions.get(neighbor_rel.target_id, 0)
                    suggestions[neighbor_rel.target_id] = current + rel.strength * neighbor_rel.strength

        sorted_suggestions = sorted(
            suggestions.items(), key=lambda x: x[1], reverse=True
        )[:10]

        result = []
        for target_id, score in sorted_suggestions:
            target = self._nodes.get(target_id)
            if target:
                result.append({
                    "node": target,
                    "connection_strength": round(score, 2),
                    "mutual_connections": self._find_mutual(node_id, target_id),
                })
        return result

    def _find_mutual(self, id_a: str, id_b: str) -> list[str]:
        """Find mutual connections between two nodes."""
        a_connections = {r.target_id for r in self._nodes[id_a].relationships}
        b_connections = {r.target_id for r in self._nodes[id_b].relationships}
        return list(a_connections & b_connections)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_nodes": len(self._nodes),
            "total_relationships": len(self._relationships),
            "node_types": list(set(
                n.entity_type.value for n in self._nodes.values()
            )),
            "avg_degree": round(
                sum(n.degree for n in self._nodes.values()) / max(len(self._nodes), 1), 2
            ),
            "relationship_types": list(set(
                r.relationship_type for r in self._relationships
            )),
        }
