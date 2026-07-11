"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import { getTenantId } from "./hooks/useTenant"

export type TriggerType = "event" | "scheduled" | "manual"
export type StepType = "send_email" | "update_crm" | "create_task" | "webhook" | "nba_recommend"

export interface WorkflowStepConfig {
  send_email?: { to: string; subject: string; body: string }
  update_crm?: { field: string; value: string }
  create_task?: { title: string; priority: string; assignee: string }
  webhook?: { url: string; method: string; body: string }
  nba_recommend?: { action_type: string; reason: string }
}

export interface WorkflowStep {
  id: string
  type: StepType
  config: WorkflowStepConfig
  condition_expression?: string
  order: number
}

export interface Workflow {
  id: string
  name: string
  description: string
  trigger_type: TriggerType
  trigger_config: Record<string, unknown>
  steps: WorkflowStep[]
  status: "active" | "draft" | "inactive"
  created_at: string
  updated_at: string
}

export interface WorkflowExecution {
  id: string
  workflow_id: string
  status: "success" | "failed" | "running"
  triggered_by: string
  started_at: string
  completed_at: string | null
  error_message: string | null
  step_results: Record<string, unknown>[]
}

export const workflowKeys = {
  all: ["workflows"] as const,
  lists: () => [...workflowKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) => [...workflowKeys.lists(), filters] as const,
  details: () => [...workflowKeys.all, "detail"] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  executions: (workflowId: string) => [...workflowKeys.all, "executions", workflowId] as const,
  templates: () => [...workflowKeys.all, "templates"] as const,
}

export function useWorkflows() {
  return useQuery({
    queryKey: workflowKeys.list(),
    queryFn: async () => {
      const res = await api.get("/api/v1/workflows", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as Workflow[]
    },
    staleTime: 15_000,
  })
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: workflowKeys.detail(id),
    queryFn: async () => {
      const res = await api.get(`/api/v1/workflows/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as Workflow
    },
    enabled: !!id,
    staleTime: 15_000,
  })
}

export function useCreateWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      const res = await api.post("/api/v1/workflows", data, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as Workflow
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.list() }),
  })
}

export function useUpdateWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<Workflow> & { id: string }) => {
      const res = await api.put(`/api/v1/workflows/${id}`, data, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as Workflow
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  })
}

export function useDeleteWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/workflows/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  })
}

export function useExecuteWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (workflowId: string) => {
      const res = await api.post(`/api/v1/workflows/${workflowId}/execute`, {}, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as WorkflowExecution
    },
    onSuccess: (_data, workflowId) => {
      qc.invalidateQueries({ queryKey: workflowKeys.executions(workflowId) })
    },
  })
}

export function useWorkflowExecutions(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.executions(workflowId),
    queryFn: async () => {
      const res = await api.get(`/api/v1/workflows/${workflowId}/executions`, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as WorkflowExecution[]
    },
    enabled: !!workflowId,
    staleTime: 10_000,
  })
}
