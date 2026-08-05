"use client";

import { useQuery } from "@tanstack/react-query";
import { getEntityActivities, getGlobalActivities } from "@/lib/api";
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

export function useGlobalActivities(filters?: {
  actor?: string;
  action?: string;
  entity_type?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: activityKeys.global(filters),
    queryFn: () => getGlobalActivities(getTenantId(), { limit: 50, ...filters }),
    staleTime: 15_000,
  });
}
