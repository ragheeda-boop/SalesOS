/**
 * Tenant Studio custom field definition HTTP (STORY-10-01 / FE-S10-01).
 * Tip POST/GET /api/v1/studio/custom-fields only. In-memory BE — no Postgres claim.
 * Not Production GO / RAG GO.
 */
import api from "./client";
import type {
  CustomFieldCreate,
  CustomFieldDefinition,
  CustomObjectSchema,
  StudioObjectKey,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/custom-fields";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listCustomFieldSchema(
  tenantId: string,
  objectKey: StudioObjectKey,
): Promise<CustomObjectSchema> {
  const resp = await api.get<CustomObjectSchema>(`${BASE}/${objectKey}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function createCustomField(
  tenantId: string,
  body: CustomFieldCreate,
): Promise<CustomFieldDefinition> {
  const resp = await api.post<CustomFieldDefinition>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
