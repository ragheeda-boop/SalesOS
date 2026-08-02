"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCustomField,
  getCustomFieldsFormSchema,
  listCustomFieldSchema,
  projectCustomFieldValues,
  type CustomFieldCreate,
  type CustomFieldValuesRequest,
  type StudioObjectKey,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useCustomFieldSchema(objectKey: StudioObjectKey) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.customFields(tenantId, objectKey),
    queryFn: () => listCustomFieldSchema(tenantId, objectKey),
    staleTime: 10_000,
  });
}

export function useCreateCustomField() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CustomFieldCreate) =>
      createCustomField(getTenantId(), body),
    onSuccess: (row) => {
      const key = row.object_key as StudioObjectKey;
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.customFields(getTenantId(), key),
      });
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.formSchema(getTenantId(), key),
      });
    },
  });
}

export function useCustomFieldsFormSchema(objectKey: StudioObjectKey) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.formSchema(tenantId, objectKey),
    queryFn: () => getCustomFieldsFormSchema(tenantId, objectKey),
    staleTime: 10_000,
  });
}

export function useProjectCustomFieldValues(objectKey: StudioObjectKey) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CustomFieldValuesRequest) =>
      projectCustomFieldValues(getTenantId(), objectKey, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.formSchema(getTenantId(), objectKey),
      });
    },
  });
}
