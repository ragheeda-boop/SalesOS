"use client";

import { useQuery } from "@tanstack/react-query";
import { getExecutiveDashboard } from "@/lib/api";
import { dashboardKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useExecutiveDashboard() {
  return useQuery({
    queryKey: dashboardKeys.exec(),
    queryFn: () => getExecutiveDashboard(getTenantId()),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}
