"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addPromptLibraryVersion,
  createPromptLibraryEntry,
  deletePromptLibraryEntry,
  getPromptLibraryEntry,
  getPromptLibraryMeta,
  listPromptLibrary,
  patchPromptLibraryMeta,
  rollbackPromptLibrary,
  type PromptCreateBody,
  type PromptMetaPatchBody,
  type PromptRollbackBody,
  type PromptVersionBody,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function usePromptLibraryMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.promptLibraryMeta(tenantId),
    queryFn: () => getPromptLibraryMeta(tenantId),
    staleTime: 60_000,
  });
}

export function usePromptLibraryList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.promptLibraryList(tenantId),
    queryFn: () => listPromptLibrary(tenantId),
    staleTime: 10_000,
  });
}

export function usePromptLibraryDetail(entryId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.promptLibraryDetail(tenantId, entryId ?? ""),
    queryFn: () => getPromptLibraryEntry(tenantId, entryId as string),
    enabled: Boolean(entryId),
    staleTime: 10_000,
  });
}

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: tenantStudioKeys.all });
}

export function useCreatePromptLibraryEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PromptCreateBody) => createPromptLibraryEntry(getTenantId(), body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function usePatchPromptLibraryMeta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, body }: { entryId: string; body: PromptMetaPatchBody }) =>
      patchPromptLibraryMeta(getTenantId(), entryId, body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useAddPromptLibraryVersion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, body }: { entryId: string; body: PromptVersionBody }) =>
      addPromptLibraryVersion(getTenantId(), entryId, body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useRollbackPromptLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, body }: { entryId: string; body: PromptRollbackBody }) =>
      rollbackPromptLibrary(getTenantId(), entryId, body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeletePromptLibraryEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) => deletePromptLibraryEntry(getTenantId(), entryId),
    onSuccess: () => invalidateAll(qc),
  });
}
