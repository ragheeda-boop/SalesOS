"use client";

import { createDashboardWidget } from "@salesos/widget-sdk";
import { CompanyScoringView } from "./CompanyScoringView";
import type { Score, Recommendation } from "@salesos/decision-platform";

interface CompanyScoringData {
  dealScore: number;
  scores: Score[];
  recommendations: Recommendation[];
  riskFlags: Score[];
}

export const CompanyScoringWidget = createDashboardWidget<CompanyScoringData>("companyScoring", {
  metadata: {
    title: "تقييم الشركات",
    description: "درجات التقييم وعواملها والتوصيات",
    permissions: ["decision:read"],
    featureFlag: { enabled: true },
    gridColumn: "span 4",
    minHeight: "320px",
  },
  render: ({ data, status, refresh }) => (
    <CompanyScoringView
      dealScore={data?.dealScore ?? 0}
      scores={data?.scores ?? []}
      recommendations={data?.recommendations ?? []}
      riskFlags={data?.riskFlags ?? []}
      isLoading={status === "loading"}
      error={status === "error" ? new Error("Failed to load company scoring") : null}
      onRefresh={refresh}
    />
  ),
});
