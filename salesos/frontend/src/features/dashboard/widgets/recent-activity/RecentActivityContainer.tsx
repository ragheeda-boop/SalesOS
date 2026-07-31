"use client";

import { useDashboardContext } from "../../_providers/dashboard-provider";
import { WidgetCard } from "../widget-card";
import { RecentActivityView } from "./RecentActivityView";

export function RecentActivityWidget() {
  const { widgets } = useDashboardContext();
  const widget = widgets.recentActivity;
  const data = widget?.data;
  return (
    <WidgetCard widget={widget} widgetId="recentActivity">
      {data ? (
        <RecentActivityView
          items={data.items ?? []}
          total={data.total ?? 0}
          onItemClick={(id) => {
            const item = data.items?.find((i) => i.id === id);
            if (item?.companyId) {
              window.location.href = `/companies/${item.companyId}`;
            }
          }}
        />
      ) : null}
    </WidgetCard>
  );
}
