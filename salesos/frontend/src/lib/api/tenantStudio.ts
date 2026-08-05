/**
 * Tenant Studio custom field HTTP (STORY-10-01 / FE-S10-01 + STORY-10-02 / FE-S10-02).
 * Tip definitions + form-schema/values. In-memory BE — no Postgres claim.
 * Not Production GO / RAG GO.
 */
import api from "./client";
import type {
  CustomFieldCreate,
  CustomFieldDefinition,
  CustomFieldsFormSchema,
  CustomFieldValuesRequest,
  CustomFieldValuesResponse,
  CustomObjectSchema,
  StudioObjectKey,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/custom-fields";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listCustomFieldSchema(
  tenantId: string,
  objectKey: StudioObjectKey
): Promise<CustomObjectSchema> {
  const resp = await api.get<CustomObjectSchema>(`${BASE}/${objectKey}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function createCustomField(
  tenantId: string,
  body: CustomFieldCreate
): Promise<CustomFieldDefinition> {
  const resp = await api.post<CustomFieldDefinition>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getCustomFieldsFormSchema(
  tenantId: string,
  objectKey: StudioObjectKey
): Promise<CustomFieldsFormSchema> {
  const resp = await api.get<CustomFieldsFormSchema>(`${BASE}/${objectKey}/form-schema`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function projectCustomFieldValues(
  tenantId: string,
  objectKey: StudioObjectKey,
  body: CustomFieldValuesRequest
): Promise<CustomFieldValuesResponse> {
  const resp = await api.post<CustomFieldValuesResponse>(`${BASE}/${objectKey}/values`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
