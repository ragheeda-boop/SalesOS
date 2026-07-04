"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompany360 } from "@/lib/api";
import { company360Keys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useCompany360(id: string) {
  return useQuery({
    queryKey: company360Keys.detail(id),
    queryFn: () => getCompany360(id, getTenantId()),
    enabled: !!id,
    staleTime: 30_000,
  });
}
