"use client";

import { useQuery } from "@tanstack/react-query";
import { getEmployee360, getMy360 } from "@/lib/api";
import { employeeKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useEmployee360(id: string) {
  return useQuery({
    queryKey: employeeKeys.detail(id),
    queryFn: () => getEmployee360(id, getTenantId()),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useMy360() {
  return useQuery({
    queryKey: employeeKeys.me(),
    queryFn: () => getMy360(getTenantId()),
    staleTime: 30_000,
  });
}
