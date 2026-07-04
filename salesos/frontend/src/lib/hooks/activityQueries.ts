"use client";

import { useQuery } from "@tanstack/react-query";
import { getEntityActivities } from "@/lib/api";
import { activityKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useEntityActivity(entityType: string, entityId: string, limit = 50) {
  return useQuery({
    queryKey: activityKeys.entity(entityType, entityId),
    queryFn: () => getEntityActivities(entityType, entityId, getTenantId(), limit),
    enabled: !!entityType && !!entityId,
    staleTime: 15_000,
  });
}
