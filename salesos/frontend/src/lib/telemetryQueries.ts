"use client"

import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"
import { getTenantId } from "./hooks/useTenant"

export interface TelemetryOverview {
  feature_adoption: {
    feature: string
    label: string
    user_count: number
    total_users: number
    adoption_pct: number
  }[]
  search_success: {
    total_searches: number
    searches_with_action: number
    success_rate: number
  }
  nba_acceptance: {
    nba_views: number
    nba_accepts: number
    nba_rejects: number
    acceptance_rate: number
  }
  time_to_insight: {
    users_with_insight: number
    total_logins: number
    avg_time_to_insight_seconds: number
    avg_time_to_insight_display: string
  }
  time_to_action: {
    users_with_action: number
    users_with_view: number
    avg_time_to_action_seconds: number
    avg_time_to_action_display: string
  }
  active_users: {
    dau: number
    wau: number
    mau: number
    period_days: number
  }
  avg_adoption_pct: number
}

export interface FeatureAdoption {
  feature: string
  label: string
  user_count: number
  total_users: number
  adoption_pct: number
}

export interface SearchSuccess {
  total_searches: number
  searches_with_action: number
  success_rate: number
}

export interface NBAAcceptance {
  nba_views: number
  nba_accepts: number
  nba_rejects: number
  acceptance_rate: number
}

export interface ActiveUsers {
  dau: number
  wau: number
  mau: number
  period_days: number
}

export const telemetryKeys = {
  all: ["telemetry"] as const,
  overview: () => [...telemetryKeys.all, "overview"] as const,
  featureAdoption: () => [...telemetryKeys.all, "feature-adoption"] as const,
  searchSuccess: () => [...telemetryKeys.all, "search-success"] as const,
  nbaAcceptance: () => [...telemetryKeys.all, "nba-acceptance"] as const,
  activeUsers: () => [...telemetryKeys.all, "active-users"] as const,
}

export function useTelemetryOverview() {
  return useQuery({
    queryKey: telemetryKeys.overview(),
    queryFn: async () => {
      const res = await api.get("/api/v1/admin/telemetry/overview", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as TelemetryOverview
    },
    refetchInterval: 60_000,
  })
}

export function useFeatureAdoption() {
  return useQuery({
    queryKey: telemetryKeys.featureAdoption(),
    queryFn: async () => {
      const res = await api.get("/api/v1/admin/telemetry/feature-adoption", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as FeatureAdoption[]
    },
    refetchInterval: 60_000,
  })
}

export function useSearchSuccess() {
  return useQuery({
    queryKey: telemetryKeys.searchSuccess(),
    queryFn: async () => {
      const res = await api.get("/api/v1/admin/telemetry/search-success", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as SearchSuccess
    },
    refetchInterval: 60_000,
  })
}

export function useNBAAcceptance() {
  return useQuery({
    queryKey: telemetryKeys.nbaAcceptance(),
    queryFn: async () => {
      const res = await api.get("/api/v1/admin/telemetry/nba-acceptance", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as NBAAcceptance
    },
    refetchInterval: 60_000,
  })
}

export function useActiveUsers() {
  return useQuery({
    queryKey: telemetryKeys.activeUsers(),
    queryFn: async () => {
      const res = await api.get("/api/v1/admin/telemetry/active-users", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as ActiveUsers
    },
    refetchInterval: 60_000,
  })
}
