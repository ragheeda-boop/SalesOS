"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import type { OpportunityStage } from "../revenue-execution/opportunity.dto";

interface CreateOpportunityInput {
  name: string;
  companyId: string;
  companyName: string;
  source?: string;
  estimatedValue: number;
  confidence?: number;
  stage?: OpportunityStage;
}

interface CreateTaskInput {
  title: string;
  priority?: string;
  company_id?: string;
  opportunity_id?: string;
  assignee_id?: string;
  source?: string;
}

export function useOpportunities(stage?: string) {
  const params = stage ? { stage } : undefined;
  return useQuery({
    queryKey: ["opportunities", stage],
    queryFn: async () => {
      const res = await api.get("/api/v1/opportunities", {
        params,
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateOpportunity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateOpportunityInput) => {
      const res = await api.post("/api/v1/opportunities", null, {
        params: {
          company_id: data.companyId,
          name: data.name,
          value: data.estimatedValue ?? 0,
        },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["opportunities"] }),
  });
}

export function useUpdateOpportunityStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, stage }: { id: string; stage: OpportunityStage }) => {
      const res = await api.put(
        `/api/v1/opportunities/${id}/stage`,
        { stage },
        {
          headers: { "X-Tenant-Id": getTenantId() },
        }
      );
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["opportunities"] }),
  });
}

export function useTasks(priority?: string, opportunityId?: string) {
  const params = {
    ...(priority ? { priority } : {}),
    ...(opportunityId ? { opportunity_id: opportunityId } : {}),
  };
  return useQuery({
    queryKey: ["tasks", priority, opportunityId],
    queryFn: async () => {
      const res = await api.get("/api/v1/tasks", {
        params: Object.keys(params).length ? params : undefined,
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateTaskInput) => {
      const res = await api.post("/api/v1/tasks", data, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.put(`/api/v1/tasks/${id}/complete`, null, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function usePipeline() {
  return useQuery({
    queryKey: ["pipeline"],
    queryFn: async () => {
      const res = await api.get("/api/v1/pipeline", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    staleTime: 30_000,
  });
}
