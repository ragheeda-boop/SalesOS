"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { getTenantId } from "./hooks/useTenant";

export type TriggerType = "event" | "scheduled" | "manual";
export type StepType =
  | "send_email"
  | "update_crm"
  | "create_task"
  | "webhook"
  | "nba_recommend"
  | "if_else"
  | "for_each"
  | "parallel"
  | "set_variable"
  | "log_message";

export interface WorkflowStepConfig {
  send_email?: { to: string; subject: string; body: string };
  update_crm?: { field: string; value: string };
  create_task?: { title: string; priority: string; assignee: string };
  webhook?: { url: string; method: string; body: string };
  nba_recommend?: { action_type: string; reason: string };
}

export interface WorkflowStep {
  id: string;
  type: StepType;
  config: WorkflowStepConfig;
  condition_expression?: string;
  order: number;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  trigger_type: TriggerType;
  trigger_config: Record<string, unknown>;
  steps: WorkflowStep[];
  status: "active" | "draft" | "inactive";
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: "success" | "failed" | "running";
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  step_results: Record<string, unknown>[];
}

type WorkflowApiStep = {
  id: string;
  step_type?: StepType;
  type?: StepType;
  config: WorkflowStepConfig;
  order: number;
  condition?: string | null;
  condition_expression?: string;
  timeout_seconds?: number | null;
  on_failure?: string;
};

type WorkflowApiWorkflow = Omit<Partial<Workflow>, "steps"> & {
  steps?: WorkflowApiStep[];
};

type WorkflowApiResponse = {
  items?: WorkflowApiWorkflow[];
  total?: number;
  next_cursor?: string | null;
};

function normalizeWorkflow(raw: WorkflowApiWorkflow): Workflow {
  return {
    id: raw.id || "",
    name: raw.name || "",
    description: raw.description || "",
    trigger_type: (raw.trigger_type as TriggerType) || "manual",
    trigger_config: raw.trigger_config || {},
    status: (raw.status as Workflow["status"]) || "draft",
    steps: (raw.steps || []).map((step) => ({
      id: step.id,
      type: step.step_type || step.type || "log_message",
      config: step.config || {},
      condition_expression: step.condition || step.condition_expression || undefined,
      order: step.order ?? 0,
    })),
    created_at: raw.created_at || new Date(0).toISOString(),
    updated_at: raw.updated_at || raw.created_at || new Date(0).toISOString(),
  };
}

export const workflowKeys = {
  all: ["workflows"] as const,
  lists: () => [...workflowKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) => [...workflowKeys.lists(), filters] as const,
  details: () => [...workflowKeys.all, "detail"] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  executions: (workflowId: string) => [...workflowKeys.all, "executions", workflowId] as const,
  templates: () => [...workflowKeys.all, "templates"] as const,
};

export function useWorkflows() {
  return useQuery({
    queryKey: workflowKeys.list(),
    queryFn: async () => {
      const res = await api.get("/api/v1/workflows", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      const payload = res.data as WorkflowApiResponse | Workflow[];
      const items: WorkflowApiWorkflow[] = Array.isArray(payload)
        ? (payload as WorkflowApiWorkflow[])
        : payload.items || [];
      return items.map(normalizeWorkflow);
    },
    staleTime: 15_000,
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: workflowKeys.detail(id),
    queryFn: async () => {
      const res = await api.get(`/api/v1/workflows/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return normalizeWorkflow(res.data as WorkflowApiWorkflow);
    },
    enabled: !!id,
    staleTime: 15_000,
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      const res = await api.post("/api/v1/workflows", data, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as Workflow;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.list() }),
  });
}

export function useUpdateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<Workflow> & { id: string }) => {
      const res = await api.put(`/api/v1/workflows/${id}`, data, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as Workflow;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  });
}

export function useDeleteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/workflows/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  });
}

export function useExecuteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (workflowId: string) => {
      const res = await api.post(
        `/api/v1/workflows/${workflowId}/execute`,
        {},
        {
          headers: { "X-Tenant-Id": getTenantId() },
        }
      );
      return res.data as WorkflowExecution;
    },
    onSuccess: (_data, workflowId) => {
      qc.invalidateQueries({ queryKey: workflowKeys.executions(workflowId) });
    },
  });
}

export function useWorkflowExecutions(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.executions(workflowId),
    queryFn: async () => {
      const res = await api.get(`/api/v1/workflows/executions`, {
        params: { workflow_id: workflowId },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return Array.isArray(res.data) ? (res.data as WorkflowExecution[]) : [];
    },
    enabled: !!workflowId,
    staleTime: 10_000,
  });
}
