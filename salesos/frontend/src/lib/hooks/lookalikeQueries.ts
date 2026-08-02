"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getLookalikeMeta,
  getLookalikeRun,
  listLookalikeRuns,
  runLookalikes,
  type LookalikeBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useLookalikeMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.lookalikeMeta(tenantId),
    queryFn: () => getLookalikeMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useLookalikeList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.lookalikeList(tenantId),
    queryFn: () => listLookalikeRuns(tenantId),
    staleTime: 10_000,
  });
}

export function useLookalikeDetail(modelId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.lookalikeDetail(tenantId, modelId ?? ""),
    queryFn: () => getLookalikeRun(tenantId, modelId as string),
    enabled: Boolean(modelId),
    staleTime: 10_000,
  });
}

export function useRunLookalikes() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LookalikeBody) => runLookalikes(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.lookalikeList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.lookalikeDetail(getTenantId(), row.id), row);
    },
  });
}
