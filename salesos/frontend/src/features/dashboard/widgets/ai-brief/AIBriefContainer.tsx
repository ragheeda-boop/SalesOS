"use client";

import { useDashboardContext } from "../../_providers/dashboard-provider";
import { WidgetCard } from "../widget-card";
import { AIBriefView } from "./AIBriefView";

export function AIBriefWidget() {
  const { widgets, refetch } = useDashboardContext();
  const widget = widgets.aiBrief;
  const data = widget?.data;
  return (
    <WidgetCard widget={widget} widgetId="aiBrief">
      {data ? (
        <AIBriefView
          summary={data.summary ?? ""}
          highlights={data.highlights ?? []}
          generatedAt={data.generatedAt}
          onRefresh={refetch}
        />
      ) : null}
    </WidgetCard>
  );
}
