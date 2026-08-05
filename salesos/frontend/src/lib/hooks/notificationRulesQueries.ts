"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  compileNotificationRule,
  listNotificationEvents,
  listNotificationRules,
  routeNotificationEvent,
  upsertNotificationRule,
  type NotificationRouteRequest,
  type NotificationRuleUpsert,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useNotificationEvents() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.notificationEvents(tenantId),
    queryFn: () => listNotificationEvents(tenantId),
    staleTime: 60_000,
  });
}

export function useNotificationRules() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.notificationRules(tenantId),
    queryFn: () => listNotificationRules(tenantId),
    staleTime: 10_000,
  });
}

export function useUpsertNotificationRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: NotificationRuleUpsert) => upsertNotificationRule(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.notificationRules(getTenantId()),
      });
    },
  });
}

export function useRouteNotificationEvent() {
  return useMutation({
    mutationFn: (body: NotificationRouteRequest) => routeNotificationEvent(getTenantId(), body),
  });
}

export function useCompileNotificationRule() {
  return useMutation({
    mutationFn: (ruleId: string) => compileNotificationRule(getTenantId(), ruleId),
  });
}
