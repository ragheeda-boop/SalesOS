"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  appendAiMemoryTurn,
  deleteAiMemoryConversation,
  getAiMemoryConversation,
  getAiMemoryMeta,
  getAiMemorySettings,
  listAiMemoryConversations,
  probeAiMemoryAdversarial,
  putAiMemorySettings,
  type AdversarialProbeBody,
  type MemorySettingsBody,
  type MemoryTurnBody,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useAiMemoryMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiMemoryMeta(tenantId),
    queryFn: () => getAiMemoryMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useAiMemorySettings() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiMemorySettings(tenantId),
    queryFn: () => getAiMemorySettings(tenantId),
    staleTime: 10_000,
  });
}

export function useAiMemoryConversations() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiMemoryList(tenantId),
    queryFn: () => listAiMemoryConversations(tenantId),
    staleTime: 10_000,
  });
}

export function useAiMemoryConversation(conversationId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiMemoryDetail(tenantId, conversationId ?? ""),
    queryFn: () => getAiMemoryConversation(tenantId, conversationId as string),
    enabled: Boolean(conversationId),
    staleTime: 10_000,
  });
}

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: tenantStudioKeys.all });
}

export function usePutAiMemorySettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: MemorySettingsBody) =>
      putAiMemorySettings(getTenantId(), body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useAppendAiMemoryTurn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      conversationId,
      body,
    }: {
      conversationId: string;
      body: MemoryTurnBody;
    }) => appendAiMemoryTurn(getTenantId(), conversationId, body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeleteAiMemoryConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: string) =>
      deleteAiMemoryConversation(getTenantId(), conversationId),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useProbeAiMemoryAdversarial() {
  return useMutation({
    mutationFn: (body: AdversarialProbeBody) =>
      probeAiMemoryAdversarial(getTenantId(), body),
  });
}
