import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getAdminHealth, getAdminMetrics, listGoldenRecords, listConflicts,
  listDlq, retryDlq, purgeDlq, getDlqStats,
  listAdminTenants, createAdminTenant, getAdminTenant, updateAdminTenant, deleteAdminTenant, getAdminTenantUsage,
  listAdminPlans, createAdminPlan, updateAdminPlan,
  listAdminLicenses, createAdminLicense,
  listAdminUsers, getAdminUser, updateAdminUser, deactivateAdminUser,
  listAdminInvoices, listAdminTransactions,
  listAdminFeatureFlags, createAdminFeatureFlag, updateAdminFeatureFlag,
  getAdminFlagTenants, toggleAdminFlagForTenant,
  listAdminJobs, getAdminJob, retryAdminJob,
  listAdminAICosts, getAdminAICostSummary, getAdminAIUsage,
  getAdminDetailedHealth, getAdminHealthHistory,
} from "@/lib/api"
import { adminKeys } from "@/lib/queryKeys"
import { useTenant } from "./useTenant"

export function useAdminHealth() {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.health(),
    queryFn: () => getAdminHealth(tenantId!),
    enabled: !!tenantId,
    refetchInterval: 15_000,
  })
}

export function useAdminMetrics() {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.metrics(),
    queryFn: () => getAdminMetrics(tenantId!),
    enabled: !!tenantId,
    refetchInterval: 15_000,
  })
}

export function useGoldenRecords(params: { page?: number; page_size?: number; status?: string } = {}) {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.goldenRecords(params),
    queryFn: () => listGoldenRecords(tenantId!, params),
    enabled: !!tenantId,
  })
}

export function useConflicts(params: { page?: number; page_size?: number; status?: string } = {}) {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.conflicts(params),
    queryFn: () => listConflicts(tenantId!, params),
    enabled: !!tenantId,
  })
}

// ─── DLQ ─────────────────────────────────────────────────────

export function useDlq(params: { page?: number; page_size?: number; status?: string; stage?: string } = {}) {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.dlq(params),
    queryFn: () => listDlq(tenantId!, params),
    enabled: !!tenantId,
    refetchInterval: 10_000,
  })
}

export function useDlqStats() {
  const { tenantId } = useTenant()
  return useQuery({
    queryKey: adminKeys.dlqStats(),
    queryFn: () => getDlqStats(tenantId!),
    enabled: !!tenantId,
    refetchInterval: 15_000,
  })
}

export function useRetryDlq() {
  const { tenantId } = useTenant()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (limit: number) => retryDlq(tenantId!, limit),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.dlq({}) })
      qc.invalidateQueries({ queryKey: adminKeys.dlqStats() })
      qc.invalidateQueries({ queryKey: adminKeys.health() })
    },
  })
}

export function usePurgeDlq() {
  const { tenantId } = useTenant()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (status?: string) => purgeDlq(tenantId!, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.dlq({}) })
      qc.invalidateQueries({ queryKey: adminKeys.dlqStats() })
    },
  })
}

// ─── Admin Portal Hooks ──────────────────────────────────────

export function useAdminTenants(filters?: Record<string, string | undefined>) {
  return useQuery({
    queryKey: adminKeys.tenants(filters as Record<string, unknown>),
    queryFn: () => listAdminTenants(filters),
  })
}

export function useAdminTenantDetail(id: string) {
  return useQuery({
    queryKey: adminKeys.tenantDetail(id),
    queryFn: () => getAdminTenant(id),
    enabled: !!id,
  })
}

export function useAdminTenantUsage(id: string) {
  return useQuery({
    queryKey: adminKeys.tenantUsage(id),
    queryFn: () => getAdminTenantUsage(id),
    enabled: !!id,
  })
}

export function useAdminPlans() {
  return useQuery({
    queryKey: adminKeys.plans(),
    queryFn: listAdminPlans,
  })
}

export function useAdminLicenses() {
  return useQuery({
    queryKey: adminKeys.licenses(),
    queryFn: listAdminLicenses,
  })
}

export function useAdminUsers(filters?: Record<string, string | undefined>) {
  return useQuery({
    queryKey: adminKeys.users(filters as Record<string, unknown>),
    queryFn: () => listAdminUsers(filters),
  })
}

export function useAdminUserDetail(id: string) {
  return useQuery({
    queryKey: adminKeys.userDetail(id),
    queryFn: () => getAdminUser(id),
    enabled: !!id,
  })
}

export function useAdminInvoices(tenantId?: string) {
  return useQuery({
    queryKey: adminKeys.invoices(tenantId),
    queryFn: () => listAdminInvoices(tenantId),
  })
}

export function useAdminTransactions(tenantId?: string) {
  return useQuery({
    queryKey: adminKeys.transactions(tenantId),
    queryFn: () => listAdminTransactions(tenantId),
  })
}

export function useAdminFeatureFlags() {
  return useQuery({
    queryKey: adminKeys.featureFlags(),
    queryFn: listAdminFeatureFlags,
  })
}

export function useAdminFlagTenants(id: string) {
  return useQuery({
    queryKey: adminKeys.featureFlagTenants(id),
    queryFn: () => getAdminFlagTenants(id),
    enabled: !!id,
  })
}

export function useAdminJobs(filters?: Record<string, string | number | undefined>) {
  return useQuery({
    queryKey: adminKeys.jobs(filters as Record<string, unknown>),
    queryFn: () => listAdminJobs(filters),
    refetchInterval: 15_000,
  })
}

export function useAdminJobDetail(id: string) {
  return useQuery({
    queryKey: adminKeys.jobDetail(id),
    queryFn: () => getAdminJob(id),
    enabled: !!id,
  })
}

export function useAdminAICosts(filters?: Record<string, string | number | undefined>) {
  return useQuery({
    queryKey: adminKeys.aiCosts(filters as Record<string, unknown>),
    queryFn: () => listAdminAICosts(filters),
  })
}

export function useAdminAICostSummary(days?: number) {
  return useQuery({
    queryKey: adminKeys.aiSummary(),
    queryFn: () => getAdminAICostSummary(days),
  })
}

export function useAdminAIUsage(days?: number) {
  return useQuery({
    queryKey: adminKeys.aiUsage(),
    queryFn: () => getAdminAIUsage(days),
  })
}

export function useAdminDetailedHealth() {
  return useQuery({
    queryKey: adminKeys.healthDetailed(),
    queryFn: getAdminDetailedHealth,
    refetchInterval: 30_000,
  })
}

export function useAdminHealthHistory(hours?: number) {
  return useQuery({
    queryKey: adminKeys.healthHistory(),
    queryFn: () => getAdminHealthHistory(hours),
  })
}

// ─── Mutations ───────────────────────────────────────────────

export function useCreateAdminTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; slug: string; domain?: string }) => createAdminTenant(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.tenants() }) },
  })
}

export function useUpdateAdminTenant(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdminTenant(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.tenants() })
      qc.invalidateQueries({ queryKey: adminKeys.tenantDetail(id) })
    },
  })
}

export function useDeleteAdminTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAdminTenant(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.tenants() }) },
  })
}

export function useCreateAdminPlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => createAdminPlan(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.plans() }) },
  })
}

export function useUpdateAdminPlan(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdminPlan(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.plans() }) },
  })
}

export function useCreateAdminLicense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { tenant_id: string; plan_id: string }) => createAdminLicense(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.licenses() }) },
  })
}

export function useUpdateAdminUser(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdminUser(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.users({}) })
      qc.invalidateQueries({ queryKey: adminKeys.userDetail(id) })
    },
  })
}

export function useDeactivateAdminUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deactivateAdminUser(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.users({}) }) },
  })
}

export function useCreateAdminFeatureFlag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { key: string; name: string; description?: string; enabled?: boolean }) => createAdminFeatureFlag(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.featureFlags() }) },
  })
}

export function useUpdateAdminFeatureFlag(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdminFeatureFlag(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.featureFlags() })
      qc.invalidateQueries({ queryKey: adminKeys.featureFlagTenants(id) })
    },
  })
}

export function useToggleAdminFlagForTenant(flagId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ tenantId, enabled }: { tenantId: string; enabled: boolean }) => toggleAdminFlagForTenant(flagId, tenantId, enabled),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.featureFlagTenants(flagId) }) },
  })
}

export function useRetryAdminJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => retryAdminJob(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminKeys.jobs({}) })
      qc.invalidateQueries({ queryKey: adminKeys.jobDetail("") })
    },
  })
}
