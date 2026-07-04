"use client";

import { useQuery } from "@tanstack/react-query";
import { unifiedSearch, type SearchParams, type SearchResponse } from "@/lib/api";
import { searchKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: searchKeys.results(params.q, params as Record<string, unknown>),
    queryFn: () => unifiedSearch(params, getTenantId()),
    enabled: params.q.length >= 2,
    staleTime: 15_000,
  });
}
