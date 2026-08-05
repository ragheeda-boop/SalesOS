"use client";

import { Skeleton } from "@salesos/ui";
import { WIDGET_CONFIG, type WidgetId } from "../_registry/widget-config";
import { DashboardGrid } from "./dashboard-grid";

export function DashboardLoading() {
  const ids = Object.keys(WIDGET_CONFIG) as WidgetId[];
  return (
    <DashboardGrid>
      {ids.map((id) => (
        <div key={id} style={{ gridColumn: WIDGET_CONFIG[id].gridColumn }}>
          <Skeleton variant="card" height={WIDGET_CONFIG[id].minHeight} className="w-full" />
        </div>
      ))}
    </DashboardGrid>
  );
}
