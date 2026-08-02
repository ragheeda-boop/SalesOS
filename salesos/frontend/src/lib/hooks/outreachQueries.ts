"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createOutreachDraft,
  getOutreachDraft,
  getOutreachMeta,
  listOutreachDrafts,
  type OutreachBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useOutreachMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.outreachMeta(tenantId),
    queryFn: () => getOutreachMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useOutreachList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.outreachList(tenantId),
    queryFn: () => listOutreachDrafts(tenantId),
    staleTime: 10_000,
  });
}

export function useOutreachDetail(runId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.outreachDetail(tenantId, runId ?? ""),
    queryFn: () => getOutreachDraft(tenantId, runId as string),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
}

export function useCreateOutreachDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OutreachBody) =>
      createOutreachDraft(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: gtmKeys.all });
    },
  });
}
