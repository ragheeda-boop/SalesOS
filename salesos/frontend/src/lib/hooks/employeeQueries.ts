"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getEmployee360,
  getMy360,
  searchEmployees,
  getEmployeeSignals,
  getEmployeeScore,
  getEmployeeTimeline,
  getEmployeePerformance,
  getEmployeeCalendarKPIs,
  getEmployeeCalendarHeatmap,
  getEmployeeEmailKPIs,
  getEmployeeEmailTopContacts,
  getEmployeeEmailDailyVolume,
  getEmployeeProductivity,
  getEmployeeRelationshipScore,
  getExecutiveSummary,
  bulkEditEmployees,
  bulkDeleteEmployees,
  exportEmployees,
  type EmployeeSearchParams,
  type EmployeeTimelineParams,
  type BulkEditEmployeesRequest,
} from "@/lib/api";
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

export function useEmployeeSearch(params: EmployeeSearchParams) {
  return useQuery({
    queryKey: employeeKeys.list(params as Record<string, unknown>),
    queryFn: () => searchEmployees(params, getTenantId()),
    staleTime: 15_000,
  });
}

export function useEmployeeSignals(employeeId: string) {
  return useQuery({
    queryKey: employeeKeys.signals(employeeId),
    queryFn: () => getEmployeeSignals(employeeId, getTenantId()),
    enabled: !!employeeId,
    staleTime: 30_000,
  });
}

export function useEmployeeScore(employeeId: string) {
  return useQuery({
    queryKey: employeeKeys.score(employeeId),
    queryFn: () => getEmployeeScore(employeeId, getTenantId()),
    enabled: !!employeeId,
    staleTime: 30_000,
  });
}

export function useEmployeeTimeline(employeeId: string, params: EmployeeTimelineParams) {
  return useQuery({
    queryKey: employeeKeys.timeline(employeeId, params as Record<string, unknown>),
    queryFn: () => getEmployeeTimeline(employeeId, params, getTenantId()),
    enabled: !!employeeId,
    staleTime: 15_000,
  });
}

export function useEmployeePerformance(employeeId: string) {
  return useQuery({
    queryKey: employeeKeys.performance(employeeId),
    queryFn: () => getEmployeePerformance(employeeId, getTenantId()),
    enabled: !!employeeId,
    staleTime: 30_000,
  });
}

export function useBulkEditEmployees() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BulkEditEmployeesRequest) => {
      return bulkEditEmployees(data, getTenantId());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: employeeKeys.lists() });
    },
  });
}

export function useBulkDeleteEmployees() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (ids: string[]) => {
      return bulkDeleteEmployees(ids, getTenantId());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: employeeKeys.lists() });
    },
  });
}

export function useExportEmployees() {
  return useMutation({
    mutationFn: async (params: Record<string, unknown>) => {
      return exportEmployees(params, getTenantId());
    },
  });
}

export function useCalendarKPIs(employeeId: string) {
  return useQuery({
    queryKey: employeeKeys.calendarKpis(employeeId),
    queryFn: () => getEmployeeCalendarKPIs(employeeId, getTenantId()),
    enabled: !!employeeId,
    staleTime: 60_000,
  });
}

export function useCalendarHeatmap(employeeId: string, days: number = 30) {
  return useQuery({
    queryKey: employeeKeys.calendarHeatmap(employeeId, days),
    queryFn: () => getEmployeeCalendarHeatmap(employeeId, getTenantId(), days),
    enabled: !!employeeId,
    staleTime: 300_000,
  });
}

export function useEmailKPIs(employeeId: string, days: number = 30) {
  return useQuery({
    queryKey: employeeKeys.emailKpis(employeeId, days),
    queryFn: () => getEmployeeEmailKPIs(employeeId, getTenantId(), days),
    enabled: !!employeeId,
    staleTime: 60_000,
  });
}

export function useEmailTopContacts(employeeId: string, limit: number = 10) {
  return useQuery({
    queryKey: employeeKeys.emailTopContacts(employeeId),
    queryFn: () => getEmployeeEmailTopContacts(employeeId, getTenantId(), limit),
    enabled: !!employeeId,
    staleTime: 300_000,
  });
}

export function useEmailDailyVolume(employeeId: string, days: number = 30) {
  return useQuery({
    queryKey: employeeKeys.emailDailyVolume(employeeId, days),
    queryFn: () => getEmployeeEmailDailyVolume(employeeId, getTenantId(), days),
    enabled: !!employeeId,
    staleTime: 120_000,
  });
}

export function useProductivity(employeeId: string, periodDays: number = 30) {
  return useQuery({
    queryKey: employeeKeys.productivity(employeeId, periodDays),
    queryFn: () => getEmployeeProductivity(employeeId, getTenantId(), periodDays),
    enabled: !!employeeId,
    staleTime: 60_000,
  });
}

export function useRelationshipScore(employeeId: string, targetType: string, targetId: string) {
  return useQuery({
    queryKey: employeeKeys.relationship(employeeId, targetType, targetId),
    queryFn: () => getEmployeeRelationshipScore(employeeId, targetType, targetId, getTenantId()),
    enabled: !!employeeId && !!targetId,
    staleTime: 120_000,
  });
}

export function useExecutiveSummary() {
  return useQuery({
    queryKey: employeeKeys.executiveSummary(),
    queryFn: () => getExecutiveSummary(getTenantId()),
    staleTime: 30_000,
  });
}
