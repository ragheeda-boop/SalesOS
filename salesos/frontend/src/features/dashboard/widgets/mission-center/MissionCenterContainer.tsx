"use client";

import { useDashboardContext } from "../../_providers/dashboard-provider";
import { WidgetCard } from "../widget-card";
import { MissionCenterView } from "./MissionCenterView";

export function MissionCenterWidget() {
  const { widgets } = useDashboardContext();
  const widget = widgets.missionCenter;
  const data = widget?.data;
  return (
    <WidgetCard widget={widget} widgetId="missionCenter">
      {data ? (
        <MissionCenterView
          companiesTracked={data.companiesTracked}
          activeDeals={data.activeDeals}
          pipelineValue={data.pipelineValue}
          signalsToday={data.signalsToday}
          decisionsPending={data.decisionsPending}
        />
      ) : null}
    </WidgetCard>
  );
}
