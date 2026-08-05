/**
 * Tenant Studio branding HTTP (STORY-10-07 / FE-S10-07).
 * Tip in-memory logo/color/name/locales. Not Production GO / RAG GO.
 */
import api from "./client";
import type { BrandingConfig, BrandingUpsert } from "./types/tenantStudio";

const BASE = "/api/v1/studio/branding";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function getBranding(tenantId: string): Promise<BrandingConfig> {
  const resp = await api.get<BrandingConfig>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertBranding(
  tenantId: string,
  body: BrandingUpsert
): Promise<BrandingConfig> {
  const resp = await api.put<BrandingConfig>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
