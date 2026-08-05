import api from "@/lib/api";
import type { SearchQuery, SearchResponse } from "@salesos/search";

function extractFilterValue(filters: SearchQuery["filters"], field: string): string | undefined {
  const f = filters?.find((f) => f.field === field && f.operator === "eq");
  return f ? String(f.value) : undefined;
}

export async function searchApi(query: SearchQuery): Promise<SearchResponse> {
  const limit = query.pageSize ?? 20;
  const offset = ((query.page ?? 1) - 1) * limit;
  const res = await api.get("/api/v1/search", {
    params: {
      q: query.text,
      strategy: "hybrid",
      limit,
      offset,
      include_facets: true,
      city: extractFilterValue(query.filters, "city"),
      region: extractFilterValue(query.filters, "region"),
      industry: extractFilterValue(query.filters, "industry"),
      status: extractFilterValue(query.filters, "status"),
    },
  });
  return res.data;
}

export async function suggestApi(prefix: string): Promise<SearchResponse["results"]> {
  const res = await api.get("/api/v1/search/suggest", {
    params: { q: prefix, limit: 5 },
  });
  return res.data?.suggestions ?? [];
}
