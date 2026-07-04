"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompany, searchCompanies, type Company, type CompanySearchParams } from "@/lib/api";
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
