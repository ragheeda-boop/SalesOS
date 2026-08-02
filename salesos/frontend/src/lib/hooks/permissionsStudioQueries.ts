"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkPermissionsCeiling,
  getPermissionsCeiling,
  listCustomRoles,
  listPermissionsCatalog,
  setPermissionsCeiling,
  upsertCustomRole,
  type CeilingCheckRequest,
  type CustomRoleUpsert,
  type SetPermissionsCeilingBody,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

function invalidatePermissions(qc: ReturnType<typeof useQueryClient>) {
  const tenantId = getTenantId();
  qc.invalidateQueries({
    queryKey: tenantStudioKeys.permissionsCatalog(tenantId),
  });
  qc.invalidateQueries({
    queryKey: tenantStudioKeys.permissionsCeiling(tenantId),
  });
  qc.invalidateQueries({
    queryKey: tenantStudioKeys.customRoles(tenantId),
  });
}

export function usePermissionsCatalog() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.permissionsCatalog(tenantId),
    queryFn: () => listPermissionsCatalog(tenantId),
    staleTime: 10_000,
  });
}

export function usePermissionsCeiling() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.permissionsCeiling(tenantId),
    queryFn: () => getPermissionsCeiling(tenantId),
    staleTime: 10_000,
  });
}

export function useCustomRoles() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.customRoles(tenantId),
    queryFn: () => listCustomRoles(tenantId),
    staleTime: 10_000,
  });
}

export function useSetPermissionsCeiling() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SetPermissionsCeilingBody) =>
      setPermissionsCeiling(getTenantId(), body),
    onSuccess: () => invalidatePermissions(qc),
  });
}

export function useUpsertCustomRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CustomRoleUpsert) =>
      upsertCustomRole(getTenantId(), body),
    onSuccess: () => invalidatePermissions(qc),
  });
}

export function useCheckPermissionsCeiling() {
  return useMutation({
    mutationFn: (body: CeilingCheckRequest) =>
      checkPermissionsCeiling(getTenantId(), body),
  });
}
