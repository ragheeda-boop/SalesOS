"use client";

import { createWidget } from "@salesos/widget-sdk";
import { useParams } from "next/navigation";
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from "../../index";
import { useCompanyIntelligence } from "@/application/company-intelligence/useCompanyIntelligence";
import { useDecisionSafe } from "@/features/revenue-execution/_providers/DecisionProvider";
import { SmartTimelineView } from "./SmartTimelineView";
import type { TimelineEvent } from "@/application/company-intelligence/company-intelligence.dto";

export const SmartTimelineWidget = createWidget({
  metadata: {
    id: "smartTimeline",
    title: "الجدول الزمني الذكي",
    category: "intelligence",
    priority: "high",
    permissions: ["company:timeline:read"],
    featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.smartTimeline.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>();
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId);
    useDecisionSafe();
    return {
      data: data?.timeline ?? null,
      status: isLoading ? ("loading" as const) : isError ? ("error" as const) : ("ready" as const),
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    };
  },
  render: ({ data }) => <SmartTimelineView events={(data ?? []) as TimelineEvent[]} />,
});
