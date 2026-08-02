"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCustomField,
  listCustomFieldSchema,
  type CustomFieldCreate,
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
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.customFields(
          getTenantId(),
          row.object_key as StudioObjectKey,
        ),
      });
    },
  });
}
