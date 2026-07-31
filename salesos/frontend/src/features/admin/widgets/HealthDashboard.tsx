"use client";

import {
  useAdminDetailedHealth,
  useAdminHealthHistory,
} from "@/lib/hooks/adminQueries";
import { HealthDashboardView } from "./HealthDashboardView";

export function HealthDashboard() {
  const { data: health, isLoading: healthLoading } = useAdminDetailedHealth();
  const { data: history, isLoading: historyLoading } = useAdminHealthHistory();

  return (
    <HealthDashboardView
      health={health}
      history={history}
      loading={healthLoading || historyLoading}
    />
  );
}
