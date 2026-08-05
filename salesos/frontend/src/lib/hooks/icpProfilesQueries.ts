"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createIcpProfile,
  getIcpMeta,
  getIcpProfile,
  listIcpProfiles,
  scoreIcpProfile,
  updateIcpProfile,
  type ICPProfileCreateBody,
  type ICPProfileUpdateBody,
  type ICPScoreBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useIcpMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.icpMeta(tenantId),
    queryFn: () => getIcpMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useIcpProfiles() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.icpList(tenantId),
    queryFn: () => listIcpProfiles(tenantId),
    staleTime: 10_000,
  });
}

export function useIcpProfile(profileId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.icpDetail(tenantId, profileId ?? ""),
    queryFn: () => getIcpProfile(tenantId, profileId as string),
    enabled: Boolean(profileId),
    staleTime: 10_000,
  });
}

export function useCreateIcpProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ICPProfileCreateBody) => createIcpProfile(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({ queryKey: gtmKeys.icpList(getTenantId()) });
      qc.setQueryData(gtmKeys.icpDetail(getTenantId(), row.id), row);
    },
  });
}

export function useUpdateIcpProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ profileId, body }: { profileId: string; body: ICPProfileUpdateBody }) =>
      updateIcpProfile(getTenantId(), profileId, body),
    onSuccess: (row) => {
      qc.invalidateQueries({ queryKey: gtmKeys.icpList(getTenantId()) });
      qc.setQueryData(gtmKeys.icpDetail(getTenantId(), row.id), row);
    },
  });
}

export function useScoreIcpProfile() {
  return useMutation({
    mutationFn: ({ profileId, body }: { profileId: string; body: ICPScoreBody }) =>
      scoreIcpProfile(getTenantId(), profileId, body),
  });
}
