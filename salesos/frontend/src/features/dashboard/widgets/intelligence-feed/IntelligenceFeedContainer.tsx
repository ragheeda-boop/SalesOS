"use client";

import { useDashboardContext } from "../../_providers/dashboard-provider";
import { WidgetCard } from "../widget-card";
import { IntelligenceFeedView } from "./IntelligenceFeedView";

export function IntelligenceFeedWidget() {
  const { widgets } = useDashboardContext();
  const widget = widgets.intelligenceFeed;
  const data = widget?.data;
  return (
    <WidgetCard widget={widget} widgetId="intelligenceFeed">
      {data ? (
        <IntelligenceFeedView
          items={data.items ?? []}
          total={data.total ?? 0}
          unseenCount={data.unseenCount ?? 0}
        />
      ) : null}
    </WidgetCard>
  );
}
