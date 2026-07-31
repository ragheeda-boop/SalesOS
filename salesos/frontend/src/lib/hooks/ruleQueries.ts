"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ruleKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export interface RuleCondition {
  field: string;
  operator: string;
  value: string;
}

export interface RuleAction {
  type: string;
  params: Record<string, unknown>;
}

export interface Rule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  domain: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

type RuleCreateInput = Omit<
  Rule,
  "id" | "tenant_id" | "created_at" | "updated_at"
>;
type RuleUpdateInput = Partial<RuleCreateInput>;

const STORAGE_KEY = "salesos_rules";

function loadRules(): Rule[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRules(rules: Rule[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(rules));
}

function getRulesForTenant(tenantId: string): Rule[] {
  return loadRules().filter((r) => r.tenant_id === tenantId);
}

function generateId(): string {
  return `rule_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function useRules(domain?: string) {
  const tenantId = getTenantId();
  return useQuery<Rule[]>({
    queryKey: ruleKeys.list(domain ? { domain } : undefined),
    queryFn: () => {
      const all = getRulesForTenant(tenantId);
      return domain ? all.filter((r) => r.domain === domain) : all;
    },
    staleTime: 0,
  });
}

export function useCreateRule() {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  return useMutation({
    mutationFn: async (input: RuleCreateInput) => {
      const now = new Date().toISOString();
      const rule: Rule = {
        ...input,
        id: generateId(),
        tenant_id: tenantId,
        created_at: now,
        updated_at: now,
      };
      const all = loadRules();
      all.push(rule);
      saveRules(all);
      return rule;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ruleKeys.lists() });
    },
  });
}

export function useUpdateRule() {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  return useMutation({
    mutationFn: async ({
      id,
      input,
    }: {
      id: string;
      input: RuleUpdateInput;
    }) => {
      const all = loadRules();
      const idx = all.findIndex((r) => r.id === id && r.tenant_id === tenantId);
      if (idx === -1) throw new Error("Rule not found");
      all[idx] = {
        ...all[idx],
        ...input,
        updated_at: new Date().toISOString(),
      };
      saveRules(all);
      return all[idx];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ruleKeys.lists() });
    },
  });
}

export function useDeleteRule() {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  return useMutation({
    mutationFn: async (id: string) => {
      const all = loadRules();
      const filtered = all.filter(
        (r) => !(r.id === id && r.tenant_id === tenantId),
      );
      saveRules(filtered);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ruleKeys.lists() });
    },
  });
}

export function useToggleRule() {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  return useMutation({
    mutationFn: async (id: string) => {
      const all = loadRules();
      const idx = all.findIndex((r) => r.id === id && r.tenant_id === tenantId);
      if (idx === -1) throw new Error("Rule not found");
      all[idx] = {
        ...all[idx],
        enabled: !all[idx].enabled,
        updated_at: new Date().toISOString(),
      };
      saveRules(all);
      return all[idx];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ruleKeys.lists() });
    },
  });
}
