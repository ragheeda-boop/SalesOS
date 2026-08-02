"use client";

import { useState } from "react";
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
import type { AiModelTierCatalogEntry } from "@/lib/api";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S12-04 — AI Model Tiers Studio (tip GET-only).
 * Does not enable feature_ai_copilot. Not Production GO / RAG GO.
 */
export function AiModelTiersStudio() {
  const { toast } = useToast();
  const [planTier, setPlanTier] = useState("starter");
  const [requestedTier, setRequestedTier] = useState("");
  const [activeRequested, setActiveRequested] = useState<string | null>(null);

  const catalogQuery = useAiModelTierCatalog();
  const defaultsQuery = useAiModelTierDefaults(planTier);
  const resolveQuery = useAiModelTiersResolve(activeRequested);

  return (
    <div className="space-y-4" data-testid="ai-model-tiers-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="ai-model-tiers-honesty"
      >
        {AI_MODEL_TIERS_HONESTY} Non-goals:{" "}
        {AI_MODEL_TIERS_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
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
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="ai-model-tiers-catalog"
      >
        <h2 className="text-sm font-semibold">Catalog (tip GET /catalog)</h2>
        {catalogQuery.isLoading ? (
          <Spinner />
        ) : catalogQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(catalogQuery.error)}
          </p>
        ) : catalogQuery.data ? (
          <>
            <p
              className="font-mono text-xs text-[var(--text-muted)]"
              data-testid="ai-model-tiers-catalog-flag"
            >
              feature_ai_copilot={String(catalogQuery.data.feature_ai_copilot)}{" "}
              · {catalogQuery.data.honesty}
            </p>
            <ul className="space-y-2 text-sm">
              {catalogQuery.data.catalog.map((row: AiModelTierCatalogEntry) => (
                <li
                  key={row.tier}
                  className="rounded border border-[var(--border-default)] px-3 py-2"
                  data-testid="ai-model-tiers-catalog-row"
                >
                  <span className="font-medium">{row.label}</span> ({row.tier})
                  · {row.provider}/{row.model}
                  <p className="text-xs text-[var(--text-muted)]">
                    {row.description}
                  </p>
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
        <h2 className="text-sm font-semibold">
          Plan defaults (tip GET /defaults)
        </h2>
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
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(defaultsQuery.error)}
          </p>
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
        <h2 className="text-sm font-semibold">
          Tenant resolve (tip GET /ai-model-tiers)
        </h2>
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
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(resolveQuery.error)}
          </p>
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
