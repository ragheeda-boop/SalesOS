"use client";

import { createWidget } from "@salesos/widget-sdk";
import { useParams } from "next/navigation";
import { useCompany360 } from "@/lib/hooks/company360Queries";
import { Company360View } from "./Company360View";

export const Company360Widget = createWidget({
  metadata: {
    id: "company360",
    title: "نظرة شاملة للشركة",
    category: "intelligence",
    priority: "critical",
    permissions: ["company:360:read"],
    featureFlag: { enabled: true, tier: "enabled" },
    minHeight: "600px",
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>();
    const { data: company360, isLoading } = useCompany360(companyId || "");
    return {
      data: { companyId: companyId || "", company360, isLoading },
      status: (companyId ? "ready" : "error") as "ready" | "error",
      lastUpdated: null,
      error: companyId ? null : new Error("Missing company ID"),
      refetch: () => {},
    };
  },
  render: ({ data }) => (
    <Company360View
      companyId={data.companyId}
      company360={data.company360}
      isLoading={data.isLoading}
    />
  ),
});
