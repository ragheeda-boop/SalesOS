"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import api from "@/lib/api";
import { useTenant } from "@/lib/hooks/useTenant";
import { Spinner, Tooltip, Badge, Button, EmptyState } from "@salesos/ui";
import {
  Search,
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Network,
  ChevronRight,
  Building2,
  User,
  Package,
  Calendar,
} from "lucide-react";

interface KNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx: number | null;
  fy: number | null;
  radius: number;
}

interface KEdge {
  source: string;
  target: string;
  label: string;
}

interface NodeDetail {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
  relationships: { target: string; targetLabel: string; relation: string }[];
}

const NODE_COLORS: Record<string, string> = {
  company: "var(--muhide-orange)",
  person: "var(--chart-3)",
  product: "#10B981",
  event: "#8B5CF6",
};

const NODE_RADIUS: Record<string, number> = {
  company: 28,
  person: 20,
  product: 22,
  event: 18,
};

const NODE_STROKE: Record<string, string> = {
  company: "#D4660F",
  person: "#2563EB",
  product: "#059669",
  event: "#7C3AED",
};

const NODE_ICONS: Record<string, typeof Building2> = {
  company: Building2,
  person: User,
  product: Package,
  event: Calendar,
};

const ENTITY_TYPES = ["company", "person", "product", "event"];

function getColor(type: string) {
  return NODE_COLORS[type.toLowerCase()] || "var(--text-muted)";
}
function getRadius(type: string) {
  return NODE_RADIUS[type.toLowerCase()] || 18;
}
function getStroke(type: string) {
  return NODE_STROKE[type.toLowerCase()] || "var(--text-muted)";
}
function getInitials(label: string) {
  const parts = label.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return label.slice(0, 2).toUpperCase();
}

function forceLayout(
  nodes: KNode[],
  edges: KEdge[],
  w: number,
  h: number,
  iters = 100,
): KNode[] {
  const n = nodes.map((nd) => ({ ...nd }));
  const map = new Map(n.map((nd) => [nd.id, nd]));
  const cx = w / 2;
  const cy = h / 2;
  n.forEach((nd, i) => {
    const a = (2 * Math.PI * i) / n.length;
    nd.x = cx + Math.cos(a) * Math.min(w, h) * 0.3;
    nd.y = cy + Math.sin(a) * Math.min(w, h) * 0.3;
    nd.vx = 0;
    nd.vy = 0;
  });
  const rep = 5500;
  const att = 0.005;
  const damp = 0.85;
  const cp = 0.01;
  for (let iter = 0; iter < iters; iter++) {
    const temp = 1 - iter / iters;
    for (let i = 0; i < n.length; i++) {
      for (let j = i + 1; j < n.length; j++) {
        const dx = n[i].x - n[j].x;
        const dy = n[i].y - n[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const f = (rep * temp) / (dist * dist);
        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        n[i].vx += fx;
        n[i].vy += fy;
        n[j].vx -= fx;
        n[j].vy -= fy;
      }
    }
    for (const e of edges) {
      const s = map.get(e.source);
      const t = map.get(e.target);
      if (!s || !t) continue;
      const dx = t.x - s.x;
      const dy = t.y - s.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = (dist - 120) * att * temp;
      s.vx += (dx / dist) * f;
      s.vy += (dy / dist) * f;
      t.vx -= (dx / dist) * f;
      t.vy -= (dy / dist) * f;
    }
    for (const nd of n) {
      nd.vx += (cx - nd.x) * cp;
      nd.vy += (cy - nd.y) * cp;
      if (nd.fx !== null) {
        nd.x = nd.fx;
        nd.y = nd.fy!;
        nd.vx = 0;
        nd.vy = 0;
      } else {
        nd.vx *= damp;
        nd.vy *= damp;
        nd.x += nd.vx;
        nd.y += nd.vy;
      }
      nd.x = Math.max(60, Math.min(w - 60, nd.x));
      nd.y = Math.max(60, Math.min(h - 60, nd.y));
    }
  }
  return n;
}

function transformGraph(data: unknown): { nodes: KNode[]; edges: KEdge[] } {
  const d = data as Record<string, unknown>;
  const rawNodes = (d.nodes || d.results || []) as Record<string, unknown>[];
  const rawEdges = (d.edges || d.relationships || []) as Record<
    string,
    unknown
  >[];
  const nodes: KNode[] = rawNodes.map((rn) => ({
    id: String(rn.id || rn.entity_id || ""),
    label: String(
      rn.name || rn.label || rn.name_ar || rn.name_en || rn.id || "",
    ),
    type: String(rn.type || rn.entity_type || "company"),
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    fx: null,
    fy: null,
    radius: getRadius(String(rn.type || rn.entity_type || "company")),
  }));
  const edges: KEdge[] = rawEdges.map((re) => ({
    source: String(re.source_id || re.source || re.from || ""),
    target: String(re.target_id || re.target || re.to || ""),
    label: String(re.type || re.relation || re.label || ""),
  }));
  return { nodes, edges };
}

function getDemoData(): { nodes: KNode[]; edges: KEdge[] } {
  return {
    nodes: [
      {
        id: "c1",
        label: "أرامكو السعودية",
        type: "company",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 28,
      },
      {
        id: "c2",
        label: "سابك",
        type: "company",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 28,
      },
      {
        id: "c3",
        label: "STC",
        type: "company",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 28,
      },
      {
        id: "c4",
        label: "الراجحي",
        type: "company",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 28,
      },
      {
        id: "c5",
        label: "دار الأركان",
        type: "company",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 28,
      },
      {
        id: "p1",
        label: "محمد العلي",
        type: "person",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 20,
      },
      {
        id: "p2",
        label: "فهد الخالدي",
        type: "person",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 20,
      },
      {
        id: "p3",
        label: "سارة المطيري",
        type: "person",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 20,
      },
      {
        id: "pr1",
        label: "نظام CRM",
        type: "product",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 22,
      },
      {
        id: "pr2",
        label: "منصة التحليلات",
        type: "product",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 22,
      },
      {
        id: "ev1",
        label: "مؤتمر التقنية 2026",
        type: "event",
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
        radius: 18,
      },
    ],
    edges: [
      { source: "c1", target: "p1", label: "WORKS_AT" },
      { source: "c1", target: "p2", label: "WORKS_AT" },
      { source: "c2", target: "p3", label: "WORKS_AT" },
      { source: "c3", target: "p1", label: "WORKS_AT" },
      { source: "c1", target: "c2", label: "COMPETES_WITH" },
      { source: "c3", target: "c5", label: "PARTNER" },
      { source: "c4", target: "pr1", label: "BUYS_FROM" },
      { source: "c5", target: "pr2", label: "BUYS_FROM" },
      { source: "c1", target: "ev1", label: "ATTENDED" },
      { source: "p1", target: "ev1", label: "ATTENDED" },
    ],
  };
}

export default function KnowledgeGraphPage() {
  const { tenantId } = useTenant();
  const svgRef = useRef<SVGSVGElement>(null);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<KNode[]>([]);
  const [edges, setEdges] = useState<KEdge[]>([]);
  const [selected, setSelected] = useState<NodeDetail | null>(null);
  const [highlighted, setHighlighted] = useState<Set<string>>(new Set());
  const [searchFilter, setSearchFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState<string[]>([]);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [svgSize, setSvgSize] = useState({ w: 900, h: 600 });
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const el = svgRef.current?.parentElement;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setSvgSize({ w: width || 900, h: height || 600 });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const layoutNodes = useMemo(
    () => forceLayout(nodes, edges, svgSize.w, svgSize.h),
    [nodes, edges, svgSize.w, svgSize.h],
  );

  const nodeMap = useMemo(
    () => new Map(layoutNodes.map((n) => [n.id, n])),
    [layoutNodes],
  );

  const typeCounts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const n of layoutNodes) c[n.type] = (c[n.type] || 0) + 1;
    return c;
  }, [layoutNodes]);

  const filteredNodeIds = useMemo(() => {
    let ids = new Set(layoutNodes.map((n) => n.id));
    if (entityFilter.length > 0) {
      ids = new Set(
        layoutNodes
          .filter((n) => entityFilter.includes(n.type))
          .map((n) => n.id),
      );
    }
    if (searchFilter) {
      const lower = searchFilter.toLowerCase();
      ids = new Set(
        layoutNodes
          .filter(
            (n) =>
              ids.has(n.id) &&
              (n.label.toLowerCase().includes(lower) ||
                n.type.toLowerCase().includes(lower)),
          )
          .map((n) => n.id),
      );
    }
    return ids;
  }, [layoutNodes, entityFilter, searchFilter]);

  const displayIds = useMemo(() => {
    if (highlighted.size > 0 && searchFilter)
      return new Set([...highlighted].filter((id) => filteredNodeIds.has(id)));
    if (highlighted.size > 0) return highlighted;
    return filteredNodeIds;
  }, [highlighted, filteredNodeIds, searchFilter]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setHasSearched(true);
    try {
      const res = await api.get("/api/v1/graph/search", {
        params: { q: query, limit: 50 },
        headers: { "X-Tenant-Id": tenantId },
      });
      const g = transformGraph(res.data);
      if (g.nodes.length > 0) {
        setNodes(g.nodes);
        setEdges(g.edges);
      } else {
        const demo = getDemoData();
        setNodes(demo.nodes);
        setEdges(demo.edges);
      }
      setSearchFilter(query);
      setSelected(null);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    } catch {
      const demo = getDemoData();
      setNodes(demo.nodes);
      setEdges(demo.edges);
      setSearchFilter(query);
      setSelected(null);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    }
    setLoading(false);
  }, [query, tenantId]);

  const handleLoadDemo = useCallback(() => {
    const demo = getDemoData();
    setNodes(demo.nodes);
    setEdges(demo.edges);
    setSearchFilter("");
    setEntityFilter([]);
    setSelected(null);
    setHighlighted(new Set());
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHasSearched(true);
  }, []);

  const handleExpandNode = useCallback(
    async (nodeId: string) => {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/graph/subgraph/${nodeId}`, {
          params: { depth: 2 },
          headers: { "X-Tenant-Id": tenantId },
        });
        const g = transformGraph(res.data);
        if (g.nodes.length > 0) {
          const existIds = new Set(nodes.map((n) => n.id));
          const newNodes = g.nodes.filter((n) => !existIds.has(n.id));
          const existKeys = new Set(
            edges.map((e) => `${e.source}->${e.target}`),
          );
          const newEdges = g.edges.filter(
            (e) => !existKeys.has(`${e.source}->${e.target}`),
          );
          setNodes((prev) => [...prev, ...newNodes]);
          setEdges((prev) => [...prev, ...newEdges]);
          setHighlighted(new Set(g.nodes.map((n) => n.id)));
          setSearchFilter("");
        }
      } catch {
        // silent
      }
      setLoading(false);
    },
    [nodes, edges, tenantId],
  );

  const handleNodeClick = useCallback(
    (node: KNode) => {
      const rels = edges.filter(
        (e) => e.source === node.id || e.target === node.id,
      );
      const relationships = rels.map((e) => {
        const isSource = e.source === node.id;
        const otherId = isSource ? e.target : e.source;
        const other = nodes.find((n) => n.id === otherId);
        return {
          target: otherId,
          targetLabel: other?.label || otherId,
          relation: e.label,
        };
      });
      setSelected({
        id: node.id,
        label: node.label,
        type: node.type,
        properties: {},
        relationships,
      });
      setHighlighted(
        new Set([
          node.id,
          ...rels.map((e) => e.source),
          ...rels.map((e) => e.target),
        ]),
      );
    },
    [edges, nodes],
  );

  const handleToggleEntityFilter = useCallback((type: string) => {
    setEntityFilter((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  }, []);

  const handleResetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHighlighted(new Set());
    setSearchFilter("");
  }, []);

  const handleBgMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      if ((e.target as SVGElement).closest("g[data-node]")) return;
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    },
    [pan],
  );

  const handleNodeMouseDown = useCallback(
    (e: React.MouseEvent, nodeId: string) => {
      e.stopPropagation();
      if (e.button !== 0) return;
      const node = nodeMap.get(nodeId);
      if (!node) return;
      const pt = svgRef.current?.createSVGPoint();
      if (!pt) return;
      pt.x = e.clientX;
      pt.y = e.clientY;
      const ctm = svgRef.current?.getScreenCTM();
      if (!ctm) return;
      const t = pt.matrixTransform(ctm.inverse());
      setDragOffset({ x: t.x - node.x, y: t.y - node.y });
      setDraggingNode(nodeId);
    },
    [nodeMap],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (draggingNode) {
        const pt = svgRef.current?.createSVGPoint();
        if (!pt) return;
        pt.x = e.clientX;
        pt.y = e.clientY;
        const ctm = svgRef.current?.getScreenCTM();
        if (!ctm) return;
        const t = pt.matrixTransform(ctm.inverse());
        const nx = (t.x - dragOffset.x - pan.x) / zoom;
        const ny = (t.y - dragOffset.y - pan.y) / zoom;
        setNodes((prev) =>
          prev.map((n) =>
            n.id === draggingNode ? { ...n, x: nx, y: ny, fx: nx, fy: ny } : n,
          ),
        );
        return;
      }
      if (isPanning)
        setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
    },
    [isPanning, panStart, draggingNode, dragOffset, pan, zoom],
  );

  const handleMouseUp = useCallback(() => {
    if (draggingNode) {
      setNodes((prev) =>
        prev.map((n) =>
          n.id === draggingNode ? { ...n, fx: null, fy: null } : n,
        ),
      );
      setDraggingNode(null);
    }
    setIsPanning(false);
  }, [draggingNode]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((prev) => Math.max(0.3, Math.min(3, prev - e.deltaY * 0.001)));
  }, []);

  const handleBgClick = useCallback(() => {
    setSelected(null);
    setHighlighted(new Set());
  }, []);

  return (
    <div className="flex h-full" dir="ltr">
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-default)] bg-[var(--bg-primary)]">
          <div className="flex items-center gap-3">
            <Network className="h-5 w-5 text-[var(--muhide-orange)]" />
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              Knowledge Graph
            </h1>
          </div>
          <div className="flex items-center gap-2">
            {ENTITY_TYPES.map((type) => {
              const Icon = NODE_ICONS[type];
              const count = typeCounts[type] || 0;
              const active = entityFilter.includes(type);
              return (
                <button
                  key={type}
                  onClick={() => handleToggleEntityFilter(type)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    active
                      ? "border-2 bg-opacity-10"
                      : "border border-[var(--border-default)] bg-[var(--bg-primary)] text-[var(--text-secondary)] hover:border-[var(--border-hover)]"
                  }`}
                  style={
                    active
                      ? {
                          borderColor: getColor(type),
                          color: getColor(type),
                          backgroundColor: `${getColor(type)}15`,
                        }
                      : undefined
                  }
                >
                  <Icon className="h-3 w-3" />
                  {type}
                  {count > 0 && (
                    <span className="text-[10px] opacity-60">({count})</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search bar */}
        <div className="px-6 py-3 border-b border-[var(--border-default)] bg-[var(--bg-primary)]">
          <div className="flex gap-2 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search entities and relationships..."
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--muhide-orange)] focus:ring-1 focus:ring-[var(--muhide-orange)] transition-colors"
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              leftIcon={
                loading ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <Search className="h-4 w-4" />
                )
              }
            >
              Search
            </Button>
          </div>
        </div>

        {/* Stats bar */}
        {nodes.length > 0 && (
          <div className="px-6 py-2 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] flex items-center gap-4 text-xs text-[var(--text-secondary)]">
            <span>
              Nodes:{" "}
              <strong className="text-[var(--text-primary)]">
                {nodes.length}
              </strong>
            </span>
            <span>
              Edges:{" "}
              <strong className="text-[var(--text-primary)]">
                {edges.length}
              </strong>
            </span>
            {searchFilter && (
              <button
                onClick={() => {
                  setSearchFilter("");
                  setHighlighted(new Set());
                }}
                className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/20 transition-colors"
              >
                <X className="h-3 w-3" />
                {searchFilter}
              </button>
            )}
          </div>
        )}

        {/* Graph canvas */}
        <div className="flex-1 relative overflow-hidden bg-[var(--bg-secondary)]">
          {/* Zoom controls */}
          <div className="absolute top-3 right-3 z-10 flex flex-col gap-1">
            <Tooltip content="Zoom in" side="left">
              <button
                onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
                className="p-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors shadow-sm"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
            </Tooltip>
            <Tooltip content="Zoom out" side="left">
              <button
                onClick={() => setZoom((z) => Math.max(0.3, z - 0.2))}
                className="p-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors shadow-sm"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
            </Tooltip>
            <Tooltip content="Reset view" side="left">
              <button
                onClick={handleResetView}
                className="p-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors shadow-sm"
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            </Tooltip>
          </div>

          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            className={
              draggingNode
                ? "cursor-grabbing"
                : "cursor-grab active:cursor-grabbing"
            }
            onMouseDown={handleBgMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            onClick={handleBgClick}
          >
            <defs>
              <marker
                id="arrow"
                markerWidth="8"
                markerHeight="6"
                refX="8"
                refY="3"
                orient="auto"
              >
                <polygon
                  points="0 0, 8 3, 0 6"
                  fill="var(--text-muted)"
                  opacity="0.5"
                />
              </marker>
              <marker
                id="arrow-active"
                markerWidth="8"
                markerHeight="6"
                refX="8"
                refY="3"
                orient="auto"
              >
                <polygon
                  points="0 0, 8 3, 0 6"
                  fill="var(--text-muted)"
                  opacity="0.8"
                />
              </marker>
              <filter id="ns" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow
                  dx="1"
                  dy="2"
                  stdDeviation="3"
                  floodOpacity="0.15"
                />
              </filter>
            </defs>

            <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}>
              {layoutNodes.length > 0 &&
                edges.map((edge, i) => {
                  const src = nodeMap.get(edge.source);
                  const tgt = nodeMap.get(edge.target);
                  if (!src || !tgt) return null;
                  const hl =
                    displayIds.has(edge.source) && displayIds.has(edge.target);
                  const mx = (src.x + tgt.x) / 2;
                  const my = (src.y + tgt.y) / 2;
                  const lw = edge.label.length * 6 + 12;
                  return (
                    <g key={`e-${i}`}>
                      <line
                        x1={src.x}
                        y1={src.y}
                        x2={tgt.x}
                        y2={tgt.y}
                        stroke={
                          hl ? "var(--text-muted)" : "var(--border-default)"
                        }
                        strokeWidth={hl ? 1.5 : 0.8}
                        strokeDasharray={hl ? "none" : "4 2"}
                        opacity={hl ? 0.8 : 0.3}
                        markerEnd={hl ? "url(#arrow-active)" : "url(#arrow)"}
                      />
                      {hl && edge.label && (
                        <>
                          <rect
                            x={mx - lw / 2}
                            y={my - 10}
                            width={lw}
                            height={14}
                            rx={3}
                            fill="var(--bg-primary)"
                            stroke="var(--border-default)"
                            strokeWidth={0.5}
                            opacity={0.9}
                          />
                          <text
                            x={mx}
                            y={my}
                            textAnchor="middle"
                            dominantBaseline="central"
                            className="fill-[var(--text-secondary)]"
                            style={{
                              fontSize: "9px",
                              fontFamily: "var(--font-ui)",
                            }}
                          >
                            {edge.label}
                          </text>
                        </>
                      )}
                    </g>
                  );
                })}

              {layoutNodes.map((node) => {
                const isActive = selected?.id === node.id;
                const isHovered = hoveredNode === node.id;
                const isDimmed =
                  displayIds.size > 0 && !displayIds.has(node.id);
                const color = getColor(node.type);
                const isDragging = draggingNode === node.id;
                return (
                  <g
                    key={node.id}
                    data-node
                    transform={`translate(${node.x},${node.y})`}
                    opacity={isDimmed ? 0.15 : 1}
                    className="cursor-pointer"
                    style={{
                      transition: isDragging ? "none" : "transform 0.15s ease",
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!isDragging) handleNodeClick(node);
                    }}
                    onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
                    onDoubleClick={(e) => {
                      e.stopPropagation();
                      handleExpandNode(node.id);
                    }}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    {isActive && (
                      <circle
                        r={node.radius + 8}
                        fill="none"
                        stroke={color}
                        strokeWidth={2}
                        opacity={0.3}
                      >
                        <animate
                          attributeName="r"
                          values={`${node.radius + 6};${node.radius + 10};${node.radius + 6}`}
                          dur="2s"
                          repeatCount="indefinite"
                        />
                      </circle>
                    )}
                    <circle
                      r={node.radius + 1}
                      fill={color}
                      opacity={0.12}
                      cx={1}
                      cy={2}
                    />
                    <circle
                      r={node.radius}
                      fill={color}
                      stroke={
                        isActive || isHovered
                          ? "var(--bg-primary)"
                          : getStroke(node.type)
                      }
                      strokeWidth={isActive ? 3 : isHovered ? 2.5 : 1.5}
                      filter={isHovered || isActive ? "url(#ns)" : undefined}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="pointer-events-none select-none"
                      style={{
                        fontSize: node.radius > 22 ? "11px" : "9px",
                        fontFamily: "var(--font-ui)",
                        fontWeight: 600,
                        fill: "white",
                      }}
                    >
                      {getInitials(node.label)}
                    </text>
                    <text
                      textAnchor="middle"
                      y={node.radius + 14}
                      className="pointer-events-none select-none"
                      style={{
                        fontSize: "11px",
                        fontFamily: "var(--font-ui)",
                        fontWeight: isActive || isHovered ? 600 : 400,
                        fill: isDimmed
                          ? "transparent"
                          : isActive
                            ? color
                            : "var(--text-primary)",
                      }}
                    >
                      {node.label.length > 18
                        ? node.label.slice(0, 16) + "\u200F\u2026"
                        : node.label}
                    </text>
                  </g>
                );
              })}
            </g>

            {nodes.length === 0 && !loading && (
              <EmptyState
                icon={<Network className="h-10 w-10" />}
                title={
                  hasSearched
                    ? "No results found"
                    : "Explore your Knowledge Graph"
                }
                description={
                  hasSearched
                    ? "Try a different search query"
                    : "Search for entities to visualize relationships, or load demo data."
                }
                action={
                  !hasSearched
                    ? { label: "Load Demo Data", onClick: handleLoadDemo }
                    : undefined
                }
              />
            )}
          </svg>

          {loading && nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-secondary)]/80">
              <div className="flex items-center gap-3 text-[var(--text-secondary)]">
                <Spinner className="h-5 w-5 text-[var(--muhide-orange)]" />
                <span className="text-sm">Loading graph...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-80 border-l border-[var(--border-default)] bg-[var(--bg-primary)] flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-default)]">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Entity Details
            </h2>
            <button
              onClick={() => {
                setSelected(null);
                setHighlighted(new Set());
              }}
              className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="px-4 py-4 border-b border-[var(--border-default)]">
            <div className="flex items-center gap-3 mb-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                style={{ background: getColor(selected.type) }}
              >
                {getInitials(selected.label)}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                  {selected.label}
                </p>
                <Badge variant="default" className="capitalize mt-0.5">
                  {selected.type}
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3">
            <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Relationships ({selected.relationships.length})
            </h3>
            {selected.relationships.length === 0 ? (
              <p className="text-xs text-[var(--text-muted)]">
                No relationships found
              </p>
            ) : (
              <div className="space-y-2">
                {selected.relationships.map((rel, i) => {
                  const targetNode = nodes.find((n) => n.id === rel.target);
                  const relType = targetNode?.type || "company";
                  return (
                    <button
                      key={i}
                      onClick={() => {
                        if (targetNode) handleNodeClick(targetNode);
                      }}
                      className="w-full text-left p-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] hover:border-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/5 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[9px] font-bold shrink-0"
                          style={{ background: getColor(relType) }}
                        >
                          {getInitials(rel.targetLabel)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                            {rel.targetLabel}
                          </p>
                          <p className="text-[10px] text-[var(--text-muted)] font-mono">
                            {rel.relation}
                          </p>
                        </div>
                        <ChevronRight className="h-3 w-3 text-[var(--text-muted)] shrink-0" />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="px-4 py-3 border-t border-[var(--border-default)]">
            <Button
              onClick={() => handleExpandNode(selected.id)}
              disabled={loading}
              leftIcon={
                loading ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )
              }
              className="w-full"
            >
              Expand Subgraph
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
