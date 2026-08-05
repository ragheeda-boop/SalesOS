"use client";

import { useState, useEffect, useCallback } from "react";
import { createWidget } from "@salesos/widget-sdk";
import { useDecision } from "../../_providers/DecisionProvider";
import type { TerritoryData } from "./types";
import type { Score } from "@salesos/decision-platform";
import { TerritoryView } from "./TerritoryView";

function mapScoresToTerritory(scores: Score[]): TerritoryData {
  // Require real territory metadata — never invent SAR values from score multipliers.
  const territories = scores
    .filter(
      (s) =>
        (s.type === "territory" || s.type === "region") && (s.metadata?.name as string | undefined)
    )
    .map((s, i) => ({
      id: `territory-${i}`,
      name: String(s.metadata?.name),
      deals: typeof s.metadata?.deals === "number" ? s.metadata.deals : 0,
      value: typeof s.metadata?.value === "number" ? s.metadata.value : 0,
      quota: typeof s.metadata?.quota === "number" ? s.metadata.quota : 0,
      attainment:
        typeof s.metadata?.attainment === "number"
          ? Math.round(s.metadata.attainment)
          : Math.round(s.value * 100),
    }));

  const coverage = territories
    .filter((t) => t.attainment >= 50)
    .map((t) => ({
      region: t.name,
      covered: true,
      salesReps:
        typeof t.deals === "number" && t.deals > 0 ? Math.max(1, Math.round(t.deals / 3)) : 0,
      opportunityValue: t.value,
    }));

  const gaps = territories
    .filter((t) => t.attainment < 50)
    .map((t) => ({
      region: t.name,
      potentialValue: Math.max(0, t.quota - t.value),
      reason: t.attainment < 30 ? "تغطية ضعيفة" : "أداء دون المستوى",
    }));

  return { territories, coverage, gaps };
}

export const TerritoryIntelligenceWidget = createWidget({
  metadata: {
    id: "territoryIntelligence",
    title: "ذكاء المناطق",
    category: "intelligence",
    priority: "high",
    permissions: ["territory:read"],
    featureFlag: { enabled: true },
    minHeight: "360px",
  },
  useData: () => {
    const decision = useDecision();
    const [state, setState] = useState<{
      data: TerritoryData | null;
      status: "loading" | "ready" | "error";
      lastUpdated: string | null;
      error: Error | null;
    }>({ data: null, status: "loading", lastUpdated: null, error: null });

    const fetchData = useCallback(async () => {
      setState((prev) => ({ ...prev, status: "loading", error: null }));
      try {
        const scores = await decision.getScores("territories", "company", "", "");
        const data = mapScoresToTerritory(scores);
        setState({
          data,
          status: "ready",
          lastUpdated: new Date().toISOString(),
          error: null,
        });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: err instanceof Error ? err : new Error(String(err)),
        }));
      }
    }, [decision]);

    useEffect(() => {
      fetchData();
    }, [fetchData]);

    return {
      data: state.data,
      status: state.status,
      lastUpdated: state.lastUpdated,
      error: state.error,
      refetch: fetchData,
    };
  },
  render: ({ data }) => <TerritoryView data={data} />,
});
