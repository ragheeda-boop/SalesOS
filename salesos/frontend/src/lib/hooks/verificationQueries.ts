"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getVerificationMeta,
  getVerificationRun,
  listVerificationRuns,
  runVerification,
  type VerificationBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useVerificationMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.verificationMeta(tenantId),
    queryFn: () => getVerificationMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useVerificationList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.verificationList(tenantId),
    queryFn: () => listVerificationRuns(tenantId),
    staleTime: 10_000,
  });
}

export function useVerificationDetail(runId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.verificationDetail(tenantId, runId ?? ""),
    queryFn: () => getVerificationRun(tenantId, runId as string),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
}

export function useRunVerification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VerificationBody) => runVerification(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.verificationList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.verificationDetail(getTenantId(), row.id), row);
    },
  });
}
