"use client";

import { useEffect, useMemo, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAiPoliciesList,
  useAiPoliciesMeta,
  useDeleteAiPolicy,
  useEvaluateAiPolicy,
  useUpsertAiPolicy,
} from "@/lib/hooks/aiPoliciesStudioQueries";
import type { AiPolicyEvaluateResult, AiPolicySet, DataClassRule } from "@/lib/api";
import {
  AI_POLICIES_HONESTY,
  AI_POLICIES_NON_GOALS,
} from "@/features/tenant-studio/aiPoliciesHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

const FALLBACK_TIERS = ["economy", "standard", "full"];
const FALLBACK_CLASSES = ["public", "internal", "pii", "confidential"];

function defaultRules(): DataClassRule[] {
  return [
    { data_class: "public", max_model_tier: "full", require_pii_scrub: false },
    {
      data_class: "internal",
      max_model_tier: "standard",
      require_pii_scrub: true,
    },
    { data_class: "pii", max_model_tier: "economy", require_pii_scrub: true },
    {
      data_class: "confidential",
      max_model_tier: "economy",
      require_pii_scrub: true,
    },
  ];
}

/**
 * FE-S12-02 — AI Policies Studio (tip STORY-12-02).
 * feature_ai_copilot False. No live LLM. Not Production GO / RAG GO.
 */
export function AiPoliciesStudio() {
  const { toast } = useToast();
  const metaQuery = useAiPoliciesMeta();
  const listQuery = useAiPoliciesList();
  const upsertMutation = useUpsertAiPolicy();
  const deleteMutation = useDeleteAiPolicy();
  const evaluateMutation = useEvaluateAiPolicy();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("Tenant AI Policy");
  const [guardrails, setGuardrails] = useState<Record<string, boolean>>({});
  const [rules, setRules] = useState<DataClassRule[]>(defaultRules());

  const [evalDataClass, setEvalDataClass] = useState("pii");
  const [evalTier, setEvalTier] = useState("full");
  const [evalSample, setEvalSample] = useState("");
  const [evalResult, setEvalResult] = useState<AiPolicyEvaluateResult | null>(null);

  const catalog = metaQuery.data?.guardrail_catalog ?? {};
  const dataClasses = metaQuery.data?.data_classes ?? FALLBACK_CLASSES;
  const modelTiers = metaQuery.data?.model_tiers ?? FALLBACK_TIERS;

  useEffect(() => {
    if (!metaQuery.data) return;
    setGuardrails((prev) => {
      if (Object.keys(prev).length > 0) return prev;
      const next: Record<string, boolean> = {};
      for (const id of Object.keys(metaQuery.data.guardrail_catalog)) {
        next[id] = true;
      }
      return next;
    });
  }, [metaQuery.data]);

  const selected = useMemo(
    () => (listQuery.data ?? []).find((r) => r.id === selectedId) ?? null,
    [listQuery.data, selectedId]
  );

  useEffect(() => {
    if (!selected) return;
    setName(selected.name);
    setGuardrails({ ...selected.guardrails });
    setRules(
      selected.data_class_rules.length
        ? selected.data_class_rules.map((r) => ({ ...r }))
        : defaultRules()
    );
  }, [selected]);

  const busy = upsertMutation.isPending || deleteMutation.isPending || evaluateMutation.isPending;

  function loadIntoForm(row: AiPolicySet) {
    setSelectedId(row.id);
    setName(row.name);
    setGuardrails({ ...row.guardrails });
    setRules(
      row.data_class_rules.length ? row.data_class_rules.map((r) => ({ ...r })) : defaultRules()
    );
    setEvalResult(null);
  }

  function clearForm() {
    setSelectedId(null);
    setName("Tenant AI Policy");
    const next: Record<string, boolean> = {};
    for (const id of Object.keys(catalog)) next[id] = true;
    setGuardrails(next);
    setRules(defaultRules());
    setEvalResult(null);
  }

  return (
    <div className="space-y-4" data-testid="ai-policies-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="ai-policies-honesty"
      >
        {AI_POLICIES_HONESTY} Non-goals: {AI_POLICIES_NON_GOALS.join("; ")}. Not Production GO / RAG
        GO.
      </p>

      {metaQuery.isLoading ? (
        <Spinner />
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="ai-policies-meta"
        >
          <p>
            {metaQuery.data.capability} · reuses=
            {(metaQuery.data.reuses ?? []).join(", ")}
          </p>
          <p data-testid="ai-policies-meta-flag">
            feature_ai_copilot={String(metaQuery.data.feature_ai_copilot)}
          </p>
          <p data-testid="ai-policies-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
        </div>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-policies-editor"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          {selectedId ? "Update policy" : "Create policy"}
        </h2>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Policy name"
          data-testid="ai-policies-name"
        />

        <div data-testid="ai-policies-guardrails">
          <p className="mb-2 text-xs font-medium text-[var(--text-muted)]">AI-GR-* toggles</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(catalog).map(([id, label]) => (
              <label
                key={id}
                className="flex items-start gap-2 text-xs text-[var(--text-primary)]"
                data-testid="ai-policies-guardrail-row"
              >
                <input
                  type="checkbox"
                  checked={Boolean(guardrails[id])}
                  onChange={(e) =>
                    setGuardrails((prev) => ({
                      ...prev,
                      [id]: e.target.checked,
                    }))
                  }
                  data-testid={`ai-policies-gr-${id}`}
                />
                <span>
                  <span className="font-mono">{id}</span> — {label}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div data-testid="ai-policies-rules">
          <p className="mb-2 text-xs font-medium text-[var(--text-muted)]">
            Data-class → max model tier
          </p>
          <div className="space-y-2">
            {rules.map((rule, idx) => (
              <div
                key={rule.data_class}
                className="flex flex-wrap items-center gap-2 text-xs"
                data-testid="ai-policies-rule-row"
              >
                <span className="w-24 font-mono">{rule.data_class}</span>
                <select
                  className="rounded border border-[var(--border)] bg-transparent px-2 py-1"
                  value={rule.max_model_tier}
                  onChange={(e) => {
                    const next = [...rules];
                    next[idx] = {
                      ...rule,
                      max_model_tier: e.target.value,
                    };
                    setRules(next);
                  }}
                  data-testid={`ai-policies-tier-${rule.data_class}`}
                >
                  {modelTiers.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <label className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={rule.require_pii_scrub}
                    onChange={(e) => {
                      const next = [...rules];
                      next[idx] = {
                        ...rule,
                        require_pii_scrub: e.target.checked,
                      };
                      setRules(next);
                    }}
                    data-testid={`ai-policies-scrub-${rule.data_class}`}
                  />
                  PII scrub
                </label>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            disabled={busy || !name.trim()}
            data-testid="ai-policies-save"
            onClick={() => {
              upsertMutation.mutate(
                {
                  id: selectedId,
                  name: name.trim(),
                  guardrails,
                  data_class_rules: rules,
                },
                {
                  onSuccess: (row) => {
                    loadIntoForm(row);
                    toast({
                      title: selectedId ? "Policy updated" : "Policy saved",
                      variant: "success",
                    });
                  },
                  onError: (err) =>
                    toast({
                      title: getApiError(err),
                      variant: "error",
                    }),
                }
              );
            }}
          >
            {selectedId ? "Save update" : "Create"}
          </Button>
          {selectedId ? (
            <Button
              variant="outline"
              disabled={busy}
              data-testid="ai-policies-new"
              onClick={clearForm}
            >
              New
            </Button>
          ) : null}
        </div>
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-policies-list"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Policies</h2>
          <Button
            variant="outline"
            size="sm"
            disabled={listQuery.isFetching}
            data-testid="ai-policies-refresh"
            onClick={() => listQuery.refetch()}
          >
            Refresh
          </Button>
        </div>
        {listQuery.isLoading ? (
          <Spinner />
        ) : listQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(listQuery.error)}</p>
        ) : (listQuery.data ?? []).length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="ai-policies-empty">
            No policies yet (tip may auto-seed default on list).
          </p>
        ) : (
          <ul className="space-y-2">
            {(listQuery.data ?? []).map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-[var(--border)] px-3 py-2 text-sm"
                data-testid="ai-policies-row"
              >
                <div>
                  <p className="font-medium text-[var(--text-primary)]">{row.name}</p>
                  <p className="font-mono text-xs text-[var(--text-muted)]">
                    {row.id} · rules={row.data_class_rules.length}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    data-testid="ai-policies-open"
                    onClick={() => loadIntoForm(row)}
                  >
                    Open
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    data-testid="ai-policies-delete"
                    onClick={() => {
                      deleteMutation.mutate(row.id, {
                        onSuccess: () => {
                          if (selectedId === row.id) clearForm();
                          toast({
                            title: "Policy deleted",
                            variant: "success",
                          });
                        },
                        onError: (err) =>
                          toast({
                            title: getApiError(err),
                            variant: "error",
                          }),
                      });
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border)] p-4"
        data-testid="ai-policies-evaluate"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Evaluate (tip POST /evaluate — no live LLM)
        </h2>
        <div className="flex flex-wrap gap-2">
          <select
            className="rounded border border-[var(--border)] bg-transparent px-2 py-1 text-sm"
            value={evalDataClass}
            onChange={(e) => setEvalDataClass(e.target.value)}
            data-testid="ai-policies-eval-class"
          >
            {dataClasses.map((dc) => (
              <option key={dc} value={dc}>
                {dc}
              </option>
            ))}
          </select>
          <select
            className="rounded border border-[var(--border)] bg-transparent px-2 py-1 text-sm"
            value={evalTier}
            onChange={(e) => setEvalTier(e.target.value)}
            data-testid="ai-policies-eval-tier"
          >
            {modelTiers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <Input
          value={evalSample}
          onChange={(e) => setEvalSample(e.target.value)}
          placeholder="Optional sample text (PII / jailbreak probe)"
          data-testid="ai-policies-eval-sample"
        />
        <Button
          disabled={busy}
          data-testid="ai-policies-eval-run"
          onClick={() => {
            evaluateMutation.mutate(
              {
                data_class: evalDataClass,
                requested_model_tier: evalTier,
                sample_text: evalSample,
                policy_id: selectedId,
              },
              {
                onSuccess: (result) => {
                  setEvalResult(result);
                  toast({
                    title: result.allowed ? "Allowed" : "Blocked",
                    variant: result.allowed ? "success" : "warning",
                  });
                },
                onError: (err) =>
                  toast({
                    title: getApiError(err),
                    variant: "error",
                  }),
              }
            );
          }}
        >
          Evaluate
        </Button>
        {evalResult ? (
          <pre
            className="overflow-auto rounded bg-[var(--surface-muted)] p-3 font-mono text-xs"
            data-testid="ai-policies-eval-result"
          >
            {JSON.stringify(evalResult, null, 2)}
          </pre>
        ) : null}
      </section>
    </div>
  );
}
