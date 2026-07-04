"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listOpportunities,
  createOpportunity,
  advanceOpportunity,
  closeWon,
  closeLost,
  type OpportunityListResponse,
} from "@/lib/api";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useOpportunities() {
  return useQuery<OpportunityListResponse>({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
}

export function useCreateOpportunity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      companyId,
      name,
      value,
    }: {
      companyId: string;
      name: string;
      value?: number;
    }) => {
      return createOpportunity(getTenantId(), companyId, name, value);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
    },
  });
}

export function useAdvanceOpportunity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      opportunityId,
      toStage,
    }: {
      opportunityId: string;
      toStage: string;
    }) => {
      return advanceOpportunity(opportunityId, toStage);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
    },
  });
}

export function useCloseWon() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      opportunityId,
      amount,
    }: {
      opportunityId: string;
      amount?: number;
    }) => {
      return closeWon(opportunityId, amount);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
    },
  });
}

export function useCloseLost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      opportunityId,
      reason,
    }: {
      opportunityId: string;
      reason?: string;
    }) => {
      return closeLost(opportunityId, reason);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
    },
  });
}
