"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createHubConnection,
  createHubMapping,
  disconnectHubConnection,
  getActiveHubMapping,
  getHubConflictPolicy,
  listHubConnections,
  listHubSyncRuns,
  putHubConflictPolicy,
  scheduleHubSync,
  testHubConnection,
  type HubConflictPolicyUpsert,
  type HubConnectionCreate,
  type HubMappingCreate,
  type HubScheduleCreate,
} from "@/lib/api";
import { integrationHubKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useHubConnections() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: integrationHubKeys.connections(tenantId),
    queryFn: () => listHubConnections(tenantId),
    staleTime: 15_000,
  });
}

export function useHubSyncRuns(connectionId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: integrationHubKeys.syncRuns(tenantId, connectionId || ""),
    queryFn: () => listHubSyncRuns(tenantId, connectionId!),
    enabled: Boolean(connectionId),
    staleTime: 10_000,
    refetchInterval: connectionId ? 30_000 : false,
  });
}

export function useHubConflictPolicy(connectionId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: integrationHubKeys.conflictPolicy(tenantId, connectionId || ""),
    queryFn: () => getHubConflictPolicy(tenantId, connectionId!),
    enabled: Boolean(connectionId),
    staleTime: 15_000,
  });
}

export function useActiveHubMapping(
  connectionId: string | null,
  model: string,
) {
  const tenantId = getTenantId();
  const trimmed = model.trim();
  return useQuery({
    queryKey: integrationHubKeys.activeMapping(
      tenantId,
      connectionId || "",
      trimmed,
    ),
    queryFn: () => getActiveHubMapping(tenantId, connectionId!, trimmed),
    enabled: Boolean(connectionId && trimmed),
    staleTime: 15_000,
  });
}

export function useCreateHubConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: HubConnectionCreate) =>
      createHubConnection(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: integrationHubKeys.connections(getTenantId()),
      });
    },
  });
}

export function useTestHubConnection() {
  return useMutation({
    mutationFn: (connectionId: string) =>
      testHubConnection(getTenantId(), connectionId),
  });
}

export function useCreateHubMapping() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      connectionId,
      body,
    }: {
      connectionId: string;
      body: HubMappingCreate;
    }) => createHubMapping(getTenantId(), connectionId, body),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({
        queryKey: integrationHubKeys.activeMapping(
          getTenantId(),
          vars.connectionId,
          vars.body.model,
        ),
      });
    },
  });
}

export function usePutHubConflictPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      connectionId,
      body,
    }: {
      connectionId: string;
      body: HubConflictPolicyUpsert;
    }) => putHubConflictPolicy(getTenantId(), connectionId, body),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({
        queryKey: integrationHubKeys.conflictPolicy(
          getTenantId(),
          vars.connectionId,
        ),
      });
    },
  });
}

export function useScheduleHubSync() {
  return useMutation({
    mutationFn: ({
      connectionId,
      body,
    }: {
      connectionId: string;
      body: HubScheduleCreate;
    }) => scheduleHubSync(getTenantId(), connectionId, body),
  });
}

export function useDisconnectHubConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      disconnectHubConnection(getTenantId(), connectionId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: integrationHubKeys.connections(getTenantId()),
      });
    },
  });
}
