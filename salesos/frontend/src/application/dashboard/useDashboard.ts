"use client"

import { useQuery } from "@tanstack/react-query"
import { getTenantId } from "@/lib/hooks/useTenant"
import { dashboardKeys } from "@/lib/queryKeys"
import { getDashboard } from "./api"
import { mapDashboard } from "./dashboard.mapper"
import type { DashboardDTO } from "./dashboard.dto"

function fetchDashboard(): Promise<DashboardDTO> {
  return getDashboard(getTenantId()).then(mapDashboard)
}

export function useDashboard() {
  return useQuery({
    queryKey: dashboardKeys.main(),
    queryFn: fetchDashboard,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}
