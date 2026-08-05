/**
 * Studio AI model tiers HTTP (STORY-12-04 / FE-S12-04).
 * Tip GET-only. Does not enable feature_ai_copilot. Not Production GO.
 */
import api from "./client";

const BASE = "/api/v1/studio/ai-model-tiers";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface AiModelTierCatalogEntry {
  tier: string;
  label: string;
  provider: string;
  model: string;
  description: string;
}

export interface AiModelTierCatalogResponse {
  catalog: AiModelTierCatalogEntry[];
  feature_ai_copilot: boolean;
  honesty: string;
}

export interface AiModelTierDefaultsResponse {
  plan_tier: string;
  ai_model_tier: { default: string; allowed: string[] };
  resolved: {
    default_tier: string;
    allowed_tiers: string[];
    selected_tier: string;
    provider: string;
    model: string;
    catalog_entry?: AiModelTierCatalogEntry;
  };
  feature_ai_copilot: boolean;
}

export interface AiModelTierResolveResponse {
  feature_ai_copilot: boolean;
  plan_tier: string;
  source: string;
  default_tier: string;
  allowed_tiers: string[];
  selected_tier: string;
  provider: string;
  model: string;
  catalog: AiModelTierCatalogEntry[];
  honesty: string;
}

export async function getAiModelTierCatalog(tenantId: string): Promise<AiModelTierCatalogResponse> {
  const resp = await api.get<AiModelTierCatalogResponse>(`${BASE}/catalog`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getAiModelTierDefaults(
  tenantId: string,
  planTier = "starter"
): Promise<AiModelTierDefaultsResponse> {
  const resp = await api.get<AiModelTierDefaultsResponse>(`${BASE}/defaults`, {
    headers: tenantHeaders(tenantId),
    params: { plan_tier: planTier },
  });
  return resp.data;
}

export async function resolveAiModelTiers(
  tenantId: string,
  requestedTier?: string | null
): Promise<AiModelTierResolveResponse> {
  const resp = await api.get<AiModelTierResolveResponse>(BASE, {
    headers: tenantHeaders(tenantId),
    params:
      requestedTier && requestedTier.trim() ? { requested_tier: requestedTier.trim() } : undefined,
  });
  return resp.data;
}
