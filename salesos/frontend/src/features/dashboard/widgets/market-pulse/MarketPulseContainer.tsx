"use client";

import { useDashboardContext } from "../../_providers/dashboard-provider";
import { WidgetCard } from "../widget-card";
import { v3CompanyHref } from "../v3-company-href";
import { MarketPulseView } from "./MarketPulseView";

export function MarketPulseWidget() {
  const { widgets } = useDashboardContext();
  const widget = widgets.marketPulse;
  const data = widget?.data;
  return (
    <WidgetCard widget={widget} widgetId="marketPulse">
      {data ? (
        <MarketPulseView
          trends={data.trends ?? []}
          topMovers={data.topMovers ?? []}
          onTrendClick={(name) => {
            window.location.href = `/market/trends/${encodeURIComponent(name)}`;
          }}
          onMoverClick={(companyId) => {
            window.location.href = v3CompanyHref(companyId);
          }}
        />
      ) : null}
    </WidgetCard>
  );
}
