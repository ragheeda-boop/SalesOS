"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getActivityDashboard,
  getCompanyEngagement,
  getEmailMetrics,
  getCalendarMetrics,
  getFollowups,
  getEngagementSummary,
} from "@/lib/api/activity-intelligence";
import type {
  ActivityDashboardDTO,
  CompanyEngagementDTO,
  EmailMetricsDTO,
  CalendarMetricsDTO,
  FollowupDashboardDTO,
  EngagementSummaryDTO,
} from "@/lib/api/types";

interface UseActivityIntelligenceOptions {
  tenantId: string;
  refreshInterval?: number;
  enabled?: boolean;
}

export function useActivityIntelligence(
  options: UseActivityIntelligenceOptions,
) {
  const { tenantId, refreshInterval = 60_000, enabled = true } = options;

  const dashboard = useQuery<ActivityDashboardDTO>({
    queryKey: ["activity", "dashboard", tenantId],
    queryFn: () => getActivityDashboard(tenantId),
    refetchInterval: refreshInterval,
    staleTime: 30_000,
    enabled: enabled && Boolean(tenantId),
  });

  const email = useQuery<EmailMetricsDTO>({
    queryKey: ["activity", "email", tenantId],
    queryFn: () => getEmailMetrics(tenantId),
    refetchInterval: refreshInterval * 2,
    staleTime: 60_000,
    enabled: enabled && Boolean(tenantId),
  });

  const calendar = useQuery<CalendarMetricsDTO>({
    queryKey: ["activity", "calendar", tenantId],
    queryFn: () => getCalendarMetrics(tenantId),
    refetchInterval: refreshInterval * 2,
    staleTime: 60_000,
    enabled: enabled && Boolean(tenantId),
  });

  const followups = useQuery<FollowupDashboardDTO>({
    queryKey: ["activity", "followups", tenantId],
    queryFn: () => getFollowups(tenantId),
    refetchInterval: refreshInterval,
    staleTime: 30_000,
    enabled: enabled && Boolean(tenantId),
  });

  const engagement = useQuery<EngagementSummaryDTO>({
    queryKey: ["activity", "engagement", tenantId],
    queryFn: () => getEngagementSummary(tenantId),
    refetchInterval: refreshInterval * 3,
    staleTime: 120_000,
    enabled: enabled && Boolean(tenantId),
  });

  const isLoading =
    dashboard.isLoading || email.isLoading || calendar.isLoading;

  return {
    dashboard: {
      data: dashboard.data ?? null,
      error: dashboard.error ?? null,
      isLoading: dashboard.isLoading,
      refresh: () => dashboard.refetch(),
    },
    email: {
      data: email.data ?? null,
      error: email.error ?? null,
      isLoading: email.isLoading,
      refresh: () => email.refetch(),
    },
    calendar: {
      data: calendar.data ?? null,
      error: calendar.error ?? null,
      isLoading: calendar.isLoading,
      refresh: () => calendar.refetch(),
    },
    followups: {
      data: followups.data ?? null,
      error: followups.error ?? null,
      isLoading: followups.isLoading,
      refresh: () => followups.refetch(),
    },
    engagement: {
      data: engagement.data ?? null,
      error: engagement.error ?? null,
      isLoading: engagement.isLoading,
      refresh: () => engagement.refetch(),
    },
    isLoading,
    refreshAll: () => {
      dashboard.refetch();
      email.refetch();
      calendar.refetch();
      followups.refetch();
      engagement.refetch();
    },
  };
}

export function useCompanyEngagement(
  companyId: string,
  tenantId: string,
  refreshInterval = 120_000,
) {
  return useQuery<CompanyEngagementDTO>({
    queryKey: ["activity", "company", tenantId, companyId],
    queryFn: () => getCompanyEngagement(companyId, tenantId),
    enabled: !!companyId,
    refetchInterval: refreshInterval,
    staleTime: 60_000,
  });
}
