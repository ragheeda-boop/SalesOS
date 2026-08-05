"use client";

import { createWidget } from "@salesos/widget-sdk";
import { useParams } from "next/navigation";
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from "../../index";
import { useCompanyIntelligence } from "@/application/company-intelligence/useCompanyIntelligence";
import { useDecisionSafe } from "@/features/revenue-execution/_providers/DecisionProvider";
import { SignalsFeedView } from "./SignalsFeedView";
import type { SignalItem } from "@/application/company-intelligence/company-intelligence.dto";

export const SignalsFeedWidget = createWidget({
  metadata: {
    id: "signalsFeed",
    title: "الإشارات",
    category: "intelligence",
    priority: "high",
    permissions: ["company:signals:read"],
    featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.signalsFeed.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>();
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId);
    useDecisionSafe();
    return {
      data: data?.signals ?? null,
      status: isLoading ? ("loading" as const) : isError ? ("error" as const) : ("ready" as const),
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    };
  },
  render: ({ data }) => <SignalsFeedView signals={(data ?? []) as SignalItem[]} />,
});
