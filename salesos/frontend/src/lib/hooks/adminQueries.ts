import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getAdminHealth, getAdminMetrics, listGoldenRecords, listConflicts, listDlq, retryDlq, purgeDlq, getDlqStats } from "@/lib/api"
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
