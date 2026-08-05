"use client";

import { createDashboardWidget } from "@salesos/widget-sdk";
import { CompanyEngagementView } from "./CompanyEngagementView";
import type { CompanyEngagementDTO } from "@/lib/api/types";

export const CompanyEngagementWidget = createDashboardWidget<CompanyEngagementDTO>(
  "companyEngagement",
  {
    metadata: {
      title: "تفاعل الشركة",
      description: "ملخص التواصل والتفاعل مع الشركة",
      permissions: ["activity:read"],
      featureFlag: { enabled: true },
      gridColumn: "span 4",
      minHeight: "280px",
    },
    render: ({ data, status, refresh }) => (
      <CompanyEngagementView
        engagement={data ?? null}
        isLoading={status === "loading"}
        error={status === "error" ? new Error("Failed to load company engagement") : null}
        onRefresh={refresh}
      />
    ),
  }
);
