"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import api from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { useTenant } from "@/lib/hooks/useTenant";
import { Spinner, Tooltip } from "@salesos/ui";
import { Search, X, ZoomIn, ZoomOut, Maximize2, Info } from "lucide-react";

interface GraphNode {
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

interface GraphEdge {
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
  contact: "var(--chart-3)",
  employee: "#10B981",
  opportunity: "#8B5CF6",
  person: "var(--chart-3)",
  contract: "#EF4444",
};

const NODE_RADIUS: Record<string, number> = {
  company: 28,
  contact: 20,
  employee: 20,
  opportunity: 22,
  person: 20,
  contract: 18,
};

const NODE_STROKE: Record<string, string> = {
  company: "#D4660F",
  contact: "#2563EB",
  employee: "#059669",
  opportunity: "#7C3AED",
  person: "#2563EB",
  contract: "#DC2626",
};

function getNodeColor(type: string): string {
  return NODE_COLORS[type.toLowerCase()] || "var(--text-muted)";
}

function getNodeRadius(type: string): number {
  return NODE_RADIUS[type.toLowerCase()] || 18;
}

function getNodeStroke(type: string): string {
  return NODE_STROKE[type.toLowerCase()] || "var(--text-muted)";
}

function getInitials(label: string): string {
  const parts = label.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return label.slice(0, 2).toUpperCase();
}

function forceSimulation(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
  iterations = 120,
): GraphNode[] {
  const n = nodes.map((nd) => ({ ...nd }));
  const nodeMap = new Map(n.map((nd) => [nd.id, nd]));
  const cx = width / 2;
  const cy = height / 2;

  n.forEach((nd, i) => {
    const angle = (2 * Math.PI * i) / n.length;
    nd.x = cx + Math.cos(angle) * Math.min(width, height) * 0.3;
    nd.y = cy + Math.sin(angle) * Math.min(width, height) * 0.3;
    nd.vx = 0;
    nd.vy = 0;
  });

  const repulsion = 6000;
  const attraction = 0.005;
  const damping = 0.85;
  const centerPull = 0.01;

  for (let iter = 0; iter < iterations; iter++) {
    const temp = 1 - iter / iterations;

    for (let i = 0; i < n.length; i++) {
      for (let j = i + 1; j < n.length; j++) {
        const dx = n[i].x - n[j].x;
        const dy = n[i].y - n[j].y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1) dist = 1;
        const force = (repulsion * temp) / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        n[i].vx += fx;
        n[i].vy += fy;
        n[j].vx -= fx;
        n[j].vy -= fy;
      }
    }

    for (const edge of edges) {
      const src = nodeMap.get(edge.source);
      const tgt = nodeMap.get(edge.target);
      if (!src || !tgt) continue;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const idealDist = 120;
      const force = (dist - idealDist) * attraction * temp;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      src.vx += fx;
      src.vy += fy;
      tgt.vx -= fx;
      tgt.vy -= fy;
    }

    for (const nd of n) {
      nd.vx += (cx - nd.x) * centerPull;
      nd.vy += (cy - nd.y) * centerPull;
    }

    for (const nd of n) {
      if (nd.fx !== null) {
        nd.x = nd.fx;
        nd.y = nd.fy!;
        nd.vx = 0;
        nd.vy = 0;
      } else {
        nd.vx *= damping;
        nd.vy *= damping;
        nd.x += nd.vx;
        nd.y += nd.vy;
      }
      const pad = 60;
      nd.x = Math.max(pad, Math.min(width - pad, nd.x));
      nd.y = Math.max(pad, Math.min(height - pad, nd.y));
    }
  }

  return n;
}

function transformSearchResults(data: unknown): {
  nodes: GraphNode[];
  edges: GraphEdge[];
} {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const seen = new Set<string>();

  const items =
    (data as Record<string, unknown>)?.results ||
    (data as Record<string, unknown>)?.nodes ||
    (Array.isArray(data) ? data : []);

  if (!Array.isArray(items)) return { nodes, edges };

  for (const item of items) {
    const r = item as Record<string, unknown>;
    const id = String(r.id || r.entity_id || crypto.randomUUID());
    const name = String(r.name || r.label || r.name_ar || r.name_en || id);
    const type = String(r.type || r.entity_type || "company");

    if (seen.has(id)) continue;
    seen.add(id);

    nodes.push({
      id,
      label: name,
      type,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: getNodeRadius(type),
    });

    if (Array.isArray(r.relationships)) {
      for (const rel of r.relationships) {
        const relRecord = rel as Record<string, unknown>;
        const targetId = String(relRecord.target_id || relRecord.target || "");
        const targetLabel = String(
          relRecord.target_label || relRecord.target_name || targetId,
        );
        const relType = String(
          relRecord.type || relRecord.relation || relRecord.label || "related",
        );
        if (targetId && !seen.has(targetId)) {
          seen.add(targetId);
          nodes.push({
            id: targetId,
            label: targetLabel,
            type: String(relRecord.target_type || "company"),
            x: 0,
            y: 0,
            vx: 0,
            vy: 0,
            fx: null,
            fy: null,
            radius: getNodeRadius(String(relRecord.target_type || "company")),
          });
        }
        if (targetId) {
          edges.push({ source: id, target: targetId, label: relType });
        }
      }
    }

    if (r.company_id && r.company_id !== id) {
      const cid = String(r.company_id);
      if (!seen.has(cid)) {
        seen.add(cid);
        nodes.push({
          id: cid,
          label: String(r.company_name || cid),
          type: "company",
          x: 0,
          y: 0,
          vx: 0,
          vy: 0,
          fx: null,
          fy: null,
          radius: getNodeRadius("company"),
        });
      }
      edges.push({ source: cid, target: id, label: "has_contact" });
    }
  }

  return { nodes, edges };
}

function transformSubgraph(data: unknown): {
  nodes: GraphNode[];
  edges: GraphEdge[];
} {
  const d = data as Record<string, unknown>;
  const rawNodes = (d.nodes || []) as Record<string, unknown>[];
  const rawEdges = (d.edges || []) as Record<string, unknown>[];

  const nodes: GraphNode[] = rawNodes.map((rn) => ({
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
    radius: getNodeRadius(String(rn.type || rn.entity_type || "company")),
  }));

  const edges: GraphEdge[] = rawEdges.map((re) => ({
    source: String(re.source_id || re.source || re.from || ""),
    target: String(re.target_id || re.target || re.to || ""),
    label: String(re.type || re.relation || re.label || ""),
  }));

  return { nodes, edges };
}

function getDemoData(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [
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
      id: "ct1",
      label: "محمد العلي",
      type: "contact",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "ct2",
      label: "فهد الخالدي",
      type: "contact",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "ct3",
      label: "سارة المطيري",
      type: "contact",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "ct4",
      label: "عبدالله الشمري",
      type: "contact",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "e1",
      label: "أحمد السبيعي",
      type: "employee",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "e2",
      label: "نورة الحربي",
      type: "employee",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 20,
    },
    {
      id: "o1",
      label: "صفقة التوريد 2024",
      type: "opportunity",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 22,
    },
    {
      id: "o2",
      label: "مشروع البنية التحتية",
      type: "opportunity",
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      radius: 22,
    },
  ];
  const edges: GraphEdge[] = [
    { source: "c1", target: "ct1", label: "has_contact" },
    { source: "c1", target: "ct2", label: "has_contact" },
    { source: "c2", target: "ct3", label: "has_contact" },
    { source: "c3", target: "ct4", label: "has_contact" },
    { source: "c4", target: "ct1", label: "has_contact" },
    { source: "e1", target: "c1", label: "assigned_to" },
    { source: "e1", target: "c2", label: "assigned_to" },
    { source: "e2", target: "c3", label: "assigned_to" },
    { source: "e2", target: "c5", label: "assigned_to" },
    { source: "o1", target: "c1", label: "belongs_to" },
    { source: "o2", target: "c3", label: "belongs_to" },
    { source: "o1", target: "e1", label: "owned_by" },
    { source: "o2", target: "e2", label: "owned_by" },
    { source: "c1", target: "c2", label: "competitor" },
    { source: "c3", target: "c5", label: "partner" },
  ];
  return { nodes, edges };
}

export default function KnowledgeGraphPage() {
  const { t } = useTranslation();
  const { tenantId } = useTenant();
  const svgRef = useRef<SVGSVGElement>(null);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeDetail | null>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());
  const [searchFilter, setSearchFilter] = useState("");
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
    () => forceSimulation(graphNodes, graphEdges, svgSize.w, svgSize.h),
    [graphNodes, graphEdges, svgSize.w, svgSize.h],
  );

  const nodeMap = useMemo(
    () => new Map(layoutNodes.map((n) => [n.id, n])),
    [layoutNodes],
  );

  const filteredNodeIds = useMemo(() => {
    if (!searchFilter) return new Set(layoutNodes.map((n) => n.id));
    const lower = searchFilter.toLowerCase();
    return new Set(
      layoutNodes
        .filter(
          (n) =>
            n.label.toLowerCase().includes(lower) ||
            n.type.toLowerCase().includes(lower),
        )
        .map((n) => n.id),
    );
  }, [layoutNodes, searchFilter]);

  const displayNodeIds = useMemo(() => {
    if (highlightedIds.size > 0 && searchFilter) {
      return new Set(
        [...highlightedIds].filter((id) => filteredNodeIds.has(id)),
      );
    }
    if (highlightedIds.size > 0) return highlightedIds;
    return filteredNodeIds;
  }, [highlightedIds, filteredNodeIds, searchFilter]);

  const nodeTypeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const n of layoutNodes) {
      counts[n.type] = (counts[n.type] || 0) + 1;
    }
    return counts;
  }, [layoutNodes]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setHasSearched(true);
    try {
      const res = await api.get("/api/v1/graph/search", {
        params: { q: query, limit: 50 },
        headers: { "X-Tenant-Id": tenantId },
      });
      const { nodes, edges } = transformSearchResults(res.data);
      if (nodes.length > 0) {
        setGraphNodes(nodes);
        setGraphEdges(edges);
      } else {
        setGraphNodes([]);
        setGraphEdges([]);
      }
      setSearchFilter(query);
      setSelectedNode(null);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    } catch {
      setGraphNodes([]);
      setGraphEdges([]);
      setSearchFilter(query);
      setSelectedNode(null);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    }
    setLoading(false);
  }, [query, tenantId]);

  const handleLoadDemo = useCallback(() => {
    const demo = getDemoData();
    setGraphNodes(demo.nodes);
    setGraphEdges(demo.edges);
    setSearchFilter("");
    setSelectedNode(null);
    setHighlightedIds(new Set());
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
        const { nodes, edges } = transformSubgraph(res.data);
        if (nodes.length > 0) {
          const existingIds = new Set(graphNodes.map((n) => n.id));
          const newNodes = nodes.filter((n) => !existingIds.has(n.id));
          const existingEdgeKeys = new Set(
            graphEdges.map((e) => `${e.source}->${e.target}`),
          );
          const newEdges = edges.filter(
            (e) => !existingEdgeKeys.has(`${e.source}->${e.target}`),
          );
          setGraphNodes((prev) => [...prev, ...newNodes]);
          setGraphEdges((prev) => [...prev, ...newEdges]);
          const related = new Set(nodes.map((n) => n.id));
          setHighlightedIds(related);
          setSearchFilter("");
        }
      } catch {
        // silent
      }
      setLoading(false);
    },
    [graphNodes, graphEdges, tenantId],
  );

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      const relatedEdges = graphEdges.filter(
        (e) => e.source === node.id || e.target === node.id,
      );
      const relationships = relatedEdges.map((e) => {
        const isSource = e.source === node.id;
        const otherId = isSource ? e.target : e.source;
        const otherNode = graphNodes.find((n) => n.id === otherId);
        return {
          target: otherId,
          targetLabel: otherNode?.label || otherId,
          relation: e.label,
        };
      });

      setSelectedNode({
        id: node.id,
        label: node.label,
        type: node.type,
        properties: {},
        relationships,
      });

      const related = new Set([
        node.id,
        ...relatedEdges.map((e) => e.source),
        ...relatedEdges.map((e) => e.target),
      ]);
      setHighlightedIds(related);
    },
    [graphEdges, graphNodes],
  );

  const handleResetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHighlightedIds(new Set());
    setSearchFilter("");
  }, []);

  const handleBgMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      const target = e.target as SVGElement;
      if (target.closest("g[data-node]")) return;
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
      const svgPoint = svgRef.current?.createSVGPoint();
      if (!svgPoint) return;
      svgPoint.x = e.clientX;
      svgPoint.y = e.clientY;
      const ctm = svgRef.current?.getScreenCTM();
      if (!ctm) return;
      const transformed = svgPoint.matrixTransform(ctm.inverse());
      setDragOffset({ x: transformed.x - node.x, y: transformed.y - node.y });
      setDraggingNode(nodeId);
    },
    [nodeMap],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (draggingNode) {
        const svgPoint = svgRef.current?.createSVGPoint();
        if (!svgPoint) return;
        svgPoint.x = e.clientX;
        svgPoint.y = e.clientY;
        const ctm = svgRef.current?.getScreenCTM();
        if (!ctm) return;
        const transformed = svgPoint.matrixTransform(ctm.inverse());
        const newX = (transformed.x - dragOffset.x - pan.x) / zoom;
        const newY = (transformed.y - dragOffset.y - pan.y) / zoom;
        setGraphNodes((prev) =>
          prev.map((n) =>
            n.id === draggingNode
              ? { ...n, x: newX, y: newY, fx: newX, fy: newY }
              : n,
          ),
        );
        return;
      }
      if (isPanning) {
        setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
      }
    },
    [isPanning, panStart, draggingNode, dragOffset, pan, zoom],
  );

  const handleMouseUp = useCallback(() => {
    if (draggingNode) {
      setGraphNodes((prev) =>
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
    setSelectedNode(null);
    setHighlightedIds(new Set());
  }, []);

  return (
    <div className="flex h-full" dir="ltr">
      <div className="flex flex-col flex-1 min-w-0">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-default)] bg-[var(--bg-primary)]">
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            {t("graph.title")}
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 text-xs text-[var(--text-secondary)]">
              <span className="flex items-center gap-1.5">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full"
                  style={{ background: "var(--muhide-orange)" }}
                />
                {t("graph.company")}
                {nodeTypeCounts.company ? (
                  <span className="text-[var(--text-muted)]">
                    ({nodeTypeCounts.company})
                  </span>
                ) : null}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500" />
                {t("graph.contact")}
                {nodeTypeCounts.contact ? (
                  <span className="text-[var(--text-muted)]">
                    ({nodeTypeCounts.contact})
                  </span>
                ) : null}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" />
                {t("graph.employee")}
                {nodeTypeCounts.employee ? (
                  <span className="text-[var(--text-muted)]">
                    ({nodeTypeCounts.employee})
                  </span>
                ) : null}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-violet-500" />
                {t("graph.opportunity")}
                {nodeTypeCounts.opportunity ? (
                  <span className="text-[var(--text-muted)]">
                    ({nodeTypeCounts.opportunity})
                  </span>
                ) : null}
              </span>
            </div>
          </div>
        </div>

        <div className="px-6 py-3 border-b border-[var(--border-default)] bg-[var(--bg-primary)]">
          <div className="flex gap-2 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder={t("graph.search_placeholder")}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--muhide-orange)] focus:ring-1 focus:ring-[var(--muhide-orange)] transition-colors"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg text-sm font-medium hover:brightness-90 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <Spinner className="h-4 w-4" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              {t("common.search")}
            </button>
          </div>
        </div>

        {graphNodes.length > 0 && (
          <div className="px-6 py-2 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] flex items-center gap-4 text-xs text-[var(--text-secondary)]">
            <span>
              {t("graph.total_nodes")}:{" "}
              <strong className="text-[var(--text-primary)]">
                {graphNodes.length}
              </strong>
            </span>
            <span>
              {t("graph.total_edges")}:{" "}
              <strong className="text-[var(--text-primary)]">
                {graphEdges.length}
              </strong>
            </span>
            {searchFilter && (
              <button
                onClick={() => {
                  setSearchFilter("");
                  setHighlightedIds(new Set());
                }}
                className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/20 transition-colors"
              >
                <X className="h-3 w-3" />
                {searchFilter}
              </button>
            )}
          </div>
        )}

        <div className="flex-1 relative overflow-hidden bg-[var(--bg-secondary)]">
          <div className="absolute top-3 right-3 z-10 flex flex-col gap-1">
            <Tooltip content={t("graph.zoom_in")} side="left">
              <button
                onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
                className="p-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors shadow-sm"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
            </Tooltip>
            <Tooltip content={t("graph.zoom_out")} side="left">
              <button
                onClick={() => setZoom((z) => Math.max(0.3, z - 0.2))}
                className="p-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors shadow-sm"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
            </Tooltip>
            <Tooltip content={t("graph.reset_view")} side="left">
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
                id="arrowhead"
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
                id="arrowhead-active"
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
              <filter
                id="node-shadow"
                x="-30%"
                y="-30%"
                width="160%"
                height="160%"
              >
                <feDropShadow
                  dx="1"
                  dy="2"
                  stdDeviation="3"
                  floodOpacity="0.15"
                />
              </filter>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}>
              {layoutNodes.length > 0 &&
                graphEdges.map((edge, i) => {
                  const src = nodeMap.get(edge.source);
                  const tgt = nodeMap.get(edge.target);
                  if (!src || !tgt) return null;
                  const isHighlighted =
                    displayNodeIds.has(edge.source) &&
                    displayNodeIds.has(edge.target);
                  const midX = (src.x + tgt.x) / 2;
                  const midY = (src.y + tgt.y) / 2;
                  const edgeLabelWidth = edge.label.length * 6 + 12;
                  return (
                    <g key={`e-${i}`}>
                      <line
                        x1={src.x}
                        y1={src.y}
                        x2={tgt.x}
                        y2={tgt.y}
                        stroke={
                          isHighlighted
                            ? "var(--text-muted)"
                            : "var(--border-default)"
                        }
                        strokeWidth={isHighlighted ? 1.5 : 0.8}
                        strokeDasharray={isHighlighted ? "none" : "4 2"}
                        opacity={isHighlighted ? 0.8 : 0.3}
                        markerEnd={
                          isHighlighted
                            ? "url(#arrowhead-active)"
                            : "url(#arrowhead)"
                        }
                      />
                      {isHighlighted && edge.label && (
                        <>
                          <rect
                            x={midX - edgeLabelWidth / 2}
                            y={midY - 10}
                            width={edgeLabelWidth}
                            height={14}
                            rx={3}
                            fill="var(--bg-primary)"
                            stroke="var(--border-default)"
                            strokeWidth={0.5}
                            opacity={0.9}
                          />
                          <text
                            x={midX}
                            y={midY}
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
                const isActive = selectedNode?.id === node.id;
                const isHovered = hoveredNode === node.id;
                const isDimmed =
                  displayNodeIds.size > 0 && !displayNodeIds.has(node.id);
                const color = getNodeColor(node.type);
                const stroke = getNodeStroke(node.type);
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
                        filter="url(#glow)"
                      >
                        <animate
                          attributeName="r"
                          values={`${node.radius + 6};${node.radius + 10};${node.radius + 6}`}
                          dur="2s"
                          repeatCount="indefinite"
                        />
                        <animate
                          attributeName="opacity"
                          values="0.3;0.15;0.3"
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
                        isActive || isHovered ? "var(--bg-primary)" : stroke
                      }
                      strokeWidth={isActive ? 3 : isHovered ? 2.5 : 1.5}
                      filter={
                        isHovered || isActive ? "url(#node-shadow)" : undefined
                      }
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
                    {hoveredNode === node.id && (
                      <g
                        transform={`translate(${node.radius + 4}, ${-node.radius - 4})`}
                      >
                        <rect
                          x={-2}
                          y={-10}
                          width={node.type.length * 7 + 10}
                          height={16}
                          rx={3}
                          fill="var(--bg-primary)"
                          stroke="var(--border-default)"
                          strokeWidth={0.5}
                        />
                        <text
                          textAnchor="start"
                          dominantBaseline="central"
                          style={{
                            fontSize: "9px",
                            fontFamily: "var(--font-ui)",
                            fill: "var(--text-secondary)",
                          }}
                        >
                          {node.type}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </g>

            {graphNodes.length === 0 && !loading && (
              <g>
                <text
                  x="50%"
                  y="45%"
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="fill-[var(--text-muted)]"
                  style={{
                    fontSize: "16px",
                    fontFamily: "var(--font-ui)",
                    fontWeight: 500,
                  }}
                >
                  {hasSearched ? t("graph.no_results") : t("graph.empty_state")}
                </text>
                {graphNodes.length === 0 && (
                  <foreignObject
                    x="50%"
                    y="54%"
                    width="300"
                    height="50"
                    style={{ transform: "translate(-150px, -25px)" }}
                  >
                    <button
                      onClick={handleLoadDemo}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] rounded-lg text-sm font-medium hover:bg-[var(--muhide-orange)]/20 transition-colors border border-[var(--muhide-orange)]/30"
                    >
                      <Info className="h-4 w-4" />
                      {t("graph.expand")}
                    </button>
                  </foreignObject>
                )}
              </g>
            )}
          </svg>

          {loading && graphNodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-secondary)]/80">
              <div className="flex items-center gap-3 text-[var(--text-secondary)]">
                <Spinner className="h-5 w-5 text-[var(--muhide-orange)]" />
                <span className="text-sm">{t("graph.loading_graph")}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedNode && (
        <div className="w-80 border-l border-[var(--border-default)] bg-[var(--bg-primary)] flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-default)]">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              {t("graph.node_details")}
            </h2>
            <button
              onClick={() => {
                setSelectedNode(null);
                setHighlightedIds(new Set());
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
                style={{ background: getNodeColor(selectedNode.type) }}
              >
                {getInitials(selectedNode.label)}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                  {selectedNode.label}
                </p>
                <p className="text-xs text-[var(--text-secondary)] capitalize">
                  {selectedNode.type}
                </p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3">
            <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              {t("graph.relationships")} ({selectedNode.relationships.length})
            </h3>
            {selectedNode.relationships.length === 0 ? (
              <p className="text-xs text-[var(--text-muted)]">
                {t("graph.no_relationships")}
              </p>
            ) : (
              <div className="space-y-2">
                {selectedNode.relationships.map((rel, i) => {
                  const targetNode = graphNodes.find(
                    (n) => n.id === rel.target,
                  );
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
                          style={{ background: getNodeColor(relType) }}
                        >
                          {getInitials(rel.targetLabel)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                            {rel.targetLabel}
                          </p>
                          <p className="text-[10px] text-[var(--text-muted)]">
                            {rel.relation}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="px-4 py-3 border-t border-[var(--border-default)]">
            <button
              onClick={() => handleExpandNode(selectedNode.id)}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[var(--muhide-orange)] text-white text-sm font-medium hover:brightness-90 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <Spinner className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
              {t("graph.expand")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
