"use client";

import { useState, useEffect, useCallback } from "react";
import { createWidget } from "@salesos/widget-sdk";
import { useDecision } from "../../_providers/DecisionProvider";
import type { ExpansionData } from "./types";
import type { Score } from "@salesos/decision-platform";
import { ExpansionView } from "./ExpansionView";

function mapScoresToExpansion(scores: Score[]): ExpansionData {
  // Require explicit metadata — never invent company names or SAR from score*1e6.
  const opportunities = scores
    .filter(
      (s) =>
        (s.type === "expansion" || s.type === "upsell") &&
        (s.metadata?.companyName as string | undefined),
    )
    .map((s) => ({
      companyName: String(s.metadata?.companyName),
      product:
        (s.metadata?.product as string) ?? s.factors?.[0]?.name ?? "منتج",
      value: typeof s.metadata?.value === "number" ? s.metadata.value : 0,
      confidence: s.value,
      reason: s.factors?.map((f) => f.name).join("، ") ?? "فرصة توسع",
    }));

  const confidenceScores = scores.filter(
    (s) =>
      s.type === "opportunity" &&
      (s.metadata?.companyName as string | undefined),
  );
  for (const s of confidenceScores) {
    opportunities.push({
      companyName: String(s.metadata?.companyName),
      product: (s.metadata?.product as string) ?? "منتج",
      value: typeof s.metadata?.value === "number" ? s.metadata.value : 0,
      confidence: s.value,
      reason: s.factors?.map((f) => f.name).join("، ") ?? "فرصة نمو",
    });
  }

  return {
    opportunities,
    totalValue: opportunities.reduce((sum, o) => sum + o.value, 0),
    avgConfidence:
      opportunities.length > 0
        ? opportunities.reduce((sum, o) => sum + o.confidence, 0) /
          opportunities.length
        : 0,
  };
}

export const ExpansionIntelligenceWidget = createWidget({
  metadata: {
    id: "expansionIntelligence",
    title: "فرص التوسع",
    category: "intelligence",
    priority: "high",
    permissions: ["expansion:read"],
    featureFlag: { enabled: true },
    minHeight: "360px",
  },
  useData: () => {
    const decision = useDecision();
    const [state, setState] = useState<{
      data: ExpansionData | null;
      status: "loading" | "ready" | "error";
      lastUpdated: string | null;
      error: Error | null;
    }>({ data: null, status: "loading", lastUpdated: null, error: null });

    const fetchData = useCallback(async () => {
      setState((prev) => ({ ...prev, status: "loading", error: null }));
      try {
        const scores = await decision.getScores(
          "expansion",
          "opportunity",
          "",
          "",
        );
        const data = mapScoresToExpansion(scores);
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
  render: ({ data }) => <ExpansionView data={data} />,
});
