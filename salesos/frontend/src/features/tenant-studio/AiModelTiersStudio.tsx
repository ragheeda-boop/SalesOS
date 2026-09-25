"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEffect, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAiModelTierCatalog,
  useAiModelTierDefaults,
  useAiModelTiersResolve,
} from "@/lib/hooks/aiModelTiersStudioQueries";
import {
  AI_MODEL_TIERS_HONESTY,
  AI_MODEL_TIERS_NON_GOALS,
} from "@/features/tenant-studio/aiModelTiersHonesty";
import type { AdminPlan, AiModelTierCatalogEntry } from "@/lib/api";
import { useAdminPlans, useUpdateAdminPlan } from "@/lib/hooks/adminQueries";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

const MODEL_TIERS = ["economy", "standard", "full"] as const;
type ModelTierName = (typeof MODEL_TIERS)[number];

/**
 * FE-S12-04 — AI Model Tiers Studio (owner-only plan write + tenant resolver).
 * Does not enable feature_ai_copilot. Not Production GO / RAG GO.
 */
export function AiModelTiersStudio() {
  const { toast } = useToast();
  const [planTier, setPlanTier] = useState("starter");
  const [requestedTier, setRequestedTier] = useState("");
  const [activeRequested, setActiveRequested] = useState<string | null>(null);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [defaultTier, setDefaultTier] = useState<ModelTierName>("economy");
  const [allowedTiers, setAllowedTiers] = useState<ModelTierName[]>(["economy"]);

  const catalogQuery = useAiModelTierCatalog();
  const defaultsQuery = useAiModelTierDefaults(planTier);
  const resolveQuery = useAiModelTiersResolve(activeRequested);
  const plansQuery = useAdminPlans();
  const selectedPlan = plansQuery.data?.find((plan: AdminPlan) => plan.id === selectedPlanId);
  const updatePlan = useUpdateAdminPlan(selectedPlanId);

  useEffect(() => {
    if (!plansQuery.data?.length) return;
    const planId = selectedPlanId || plansQuery.data[0].id;
    const plan = plansQuery.data.find((row: AdminPlan) => row.id === planId);
    if (!plan) return;
    if (!selectedPlanId) setSelectedPlanId(plan.id);
    const entitlement = plan.entitlements?.ai_model_tier;
    const nextDefault = entitlement?.default ?? "economy";
    const nextAllowed = entitlement?.allowed?.length ? entitlement.allowed : [nextDefault];
    setDefaultTier(nextDefault);
    setAllowedTiers([...nextAllowed]);
  }, [plansQuery.data, selectedPlanId]);

  const savePlanTier = async () => {
    if (!selectedPlan?.entitlements || !allowedTiers.length || !allowedTiers.includes(defaultTier)) {
      return;
    }
    try {
      await updatePlan.mutateAsync({
        entitlements: {
          ...selectedPlan.entitlements,
          ai_model_tier: { default: defaultTier, allowed: allowedTiers },
        },
      });
      toast({ title: "Plan model tiers saved", variant: "success" });
    } catch (err: unknown) {
      toast({ title: getApiError(err), variant: "error" });
    }
  };

  return (
    <div className="space-y-4" data-testid="ai-model-tiers-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="ai-model-tiers-honesty"
      >
        {AI_MODEL_TIERS_HONESTY} Non-goals: {AI_MODEL_TIERS_NON_GOALS.join("; ")}. Not Production GO
        / RAG GO.
      </p>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="secondary"
          data-testid="ai-model-tiers-refresh"
          onClick={() => {
            void catalogQuery.refetch();
            void defaultsQuery.refetch();
            void resolveQuery.refetch();
          }}
        >
          Refresh
        </Button>
      </div>

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="ai-model-tiers-plan-config"
      >
        <h2 className="text-sm font-semibold">Configure plan entitlement</h2>
        <p className="text-xs text-[var(--text-muted)]">
          Saving requires platform owner admin access. The plan resolver enforces these limits;
          changing tiers does not enable the Copilot feature flag.
        </p>
        {plansQuery.isLoading ? (
          <Spinner />
        ) : plansQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(plansQuery.error)}</p>
        ) : plansQuery.data?.length ? (
          <>
            <label className="block max-w-md text-sm">
              Plan
              <select
                className="mt-1 block w-full rounded border border-[var(--border-default)] bg-transparent px-2 py-2"
                value={selectedPlanId}
                onChange={(event) => setSelectedPlanId(event.target.value)}
                data-testid="ai-model-tiers-plan-select"
              >
                {plansQuery.data.map((plan: AdminPlan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.name} · {plan.tier}
                  </option>
                ))}
              </select>
            </label>
            <label className="block max-w-md text-sm">
              Default model tier
              <select
                className="mt-1 block w-full rounded border border-[var(--border-default)] bg-transparent px-2 py-2"
                value={defaultTier}
                onChange={(event) => setDefaultTier(event.target.value as ModelTierName)}
                data-testid="ai-model-tiers-default-select"
              >
                {MODEL_TIERS.map((tier) => (
                  <option key={tier} value={tier}>
                    {tier}
                  </option>
                ))}
              </select>
            </label>
            <fieldset className="space-y-2">
              <legend className="text-sm">Allowed tiers</legend>
              {MODEL_TIERS.map((tier) => (
                <label key={tier} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={allowedTiers.includes(tier)}
                    onChange={(event) => {
                      const next = event.target.checked
                        ? [...allowedTiers, tier]
                        : allowedTiers.filter((item) => item !== tier);
                      setAllowedTiers(next);
                      if (!event.target.checked && defaultTier === tier && next.length) {
                        setDefaultTier(next[0]);
                      }
                    }}
                    data-testid={`ai-model-tiers-allowed-${tier}`}
                  />
                  {tier}
                </label>
              ))}
            </fieldset>
            <Button
              type="button"
              size="sm"
              disabled={
                updatePlan.isPending ||
                !selectedPlan?.entitlements ||
                !allowedTiers.length ||
                !allowedTiers.includes(defaultTier)
              }
              onClick={() => void savePlanTier()}
              data-testid="ai-model-tiers-save-plan"
            >
              {updatePlan.isPending ? "Saving…" : "Save plan tiers"}
            </Button>
          </>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">No plans are available to configure.</p>
        )}
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="ai-model-tiers-catalog"
      >
        <h2 className="text-sm font-semibold">Catalog (tip GET /catalog)</h2>
        {catalogQuery.isLoading ? (
          <Spinner />
        ) : catalogQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(catalogQuery.error)}</p>
        ) : catalogQuery.data ? (
          <>
            <p
              className="font-mono text-xs text-[var(--text-muted)]"
              data-testid="ai-model-tiers-catalog-flag"
            >
              feature_ai_copilot={String(catalogQuery.data.feature_ai_copilot)} ·{" "}
              {catalogQuery.data.honesty}
            </p>
            <ul className="space-y-2 text-sm">
              {catalogQuery.data.catalog.map((row: AiModelTierCatalogEntry) => (
                <li
                  key={row.tier}
                  className="rounded border border-[var(--border-default)] px-3 py-2"
                  data-testid="ai-model-tiers-catalog-row"
                >
                  <span className="font-medium">{row.label}</span> ({row.tier}) · {row.provider}/
                  {row.model}
                  <p className="text-xs text-[var(--text-muted)]">{row.description}</p>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="ai-model-tiers-defaults"
      >
        <h2 className="text-sm font-semibold">Plan defaults (tip GET /defaults)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="plan_tier"
            value={planTier}
            onChange={(e) => setPlanTier(e.target.value)}
            className="max-w-xs"
            data-testid="ai-model-tiers-plan-tier"
          />
          <Button
            type="button"
            size="sm"
            data-testid="ai-model-tiers-defaults-load"
            onClick={() => {
              void defaultsQuery.refetch().then((r: { error: unknown }) => {
                if (r.error) {
                  toast({
                    title: "Defaults failed",
                    description: getApiError(r.error),
                    variant: "error",
                  });
                }
              });
            }}
          >
            Load defaults
          </Button>
        </div>
        {defaultsQuery.isLoading ? (
          <Spinner />
        ) : defaultsQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(defaultsQuery.error)}</p>
        ) : defaultsQuery.data ? (
          <pre
            className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
            data-testid="ai-model-tiers-defaults-result"
          >
            {JSON.stringify(defaultsQuery.data, null, 2)}
          </pre>
        ) : null}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="ai-model-tiers-resolve"
      >
        <h2 className="text-sm font-semibold">Tenant resolve (tip GET /ai-model-tiers)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="requested_tier (optional)"
            value={requestedTier}
            onChange={(e) => setRequestedTier(e.target.value)}
            className="max-w-xs"
            data-testid="ai-model-tiers-requested"
          />
          <Button
            type="button"
            size="sm"
            data-testid="ai-model-tiers-resolve-run"
            onClick={() => {
              setActiveRequested(requestedTier.trim() || null);
            }}
          >
            Resolve for tenant
          </Button>
        </div>
        {resolveQuery.isLoading ? (
          <Spinner />
        ) : resolveQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(resolveQuery.error)}</p>
        ) : resolveQuery.data ? (
          <>
            <p
              className="font-mono text-xs text-[var(--text-muted)]"
              data-testid="ai-model-tiers-resolve-summary"
            >
              plan={resolveQuery.data.plan_tier} · source=
              {resolveQuery.data.source} · selected=
              {resolveQuery.data.selected_tier} · {resolveQuery.data.provider}/
              {resolveQuery.data.model} · feature_ai_copilot=
              {String(resolveQuery.data.feature_ai_copilot)}
            </p>
            <pre
              className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
              data-testid="ai-model-tiers-resolve-result"
            >
              {JSON.stringify(resolveQuery.data, null, 2)}
            </pre>
          </>
        ) : null}
      </section>
    </div>
  );
}
