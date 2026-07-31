"use client";

import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import {
  getCompany,
  searchCompanies,
  searchCompaniesCursor,
  type CompanySearchParams,
} from "@/lib/api";
import { companyKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useCompany(id: string) {
  return useQuery({
    queryKey: companyKeys.detail(id),
    queryFn: () => getCompany(id, getTenantId()),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useCompanySearch(params: CompanySearchParams) {
  return useQuery({
    queryKey: companyKeys.list(params as Record<string, unknown>),
    queryFn: () => searchCompanies(params, getTenantId()),
    staleTime: 10_000,
  });
}

export function useCompanySearchCursor(
  baseParams: Omit<CompanySearchParams, "cursor">,
) {
  return useInfiniteQuery({
    queryKey: [...companyKeys.lists(), "cursor", baseParams],
    queryFn: async ({ pageParam }: { pageParam: string | undefined }) => {
      const result = await searchCompaniesCursor(
        { ...baseParams, cursor: pageParam },
        getTenantId(),
      );
      return result;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.next_cursor : undefined,
  });
}
