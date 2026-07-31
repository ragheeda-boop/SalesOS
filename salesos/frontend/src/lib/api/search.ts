import api from "./client";
import type { SearchParams, SearchResponse } from "./types";

export async function unifiedSearch(
  params: SearchParams,
  tenantId: string,
): Promise<SearchResponse> {
  const response = await api.get("/api/v1/search", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
