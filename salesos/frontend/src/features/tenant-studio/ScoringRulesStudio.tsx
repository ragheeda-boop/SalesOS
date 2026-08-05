"use client";

import { useMemo, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useEvaluateScoringRule,
  useScoringRules,
  useUpsertScoringRule,
} from "@/lib/hooks/scoringRulesQueries";
import type { ScoringBoostOp, ScoringTargetType } from "@/lib/api/types/tenantStudio";
import {
  PLATFORM_DEFAULT_DIMENSION_WEIGHTS,
  SCORING_BOOST_OPS,
  SCORING_DIMENSIONS,
  SCORING_TARGET_TYPES,
} from "@/lib/api/types/tenantStudio";
import {
  SCORING_RULES_HONESTY,
  SCORING_RULES_NON_GOALS,
} from "@/features/tenant-studio/scoringRulesHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-04 — Scoring Rules Studio against tip STORY-10-04 HTTP.
 * Deterministic in-memory rules. Not Production GO / RAG GO. TenantList untouched.
 */
export function ScoringRulesStudio() {
  const { toast } = useToast();
  const listQuery = useScoringRules();
  const upsertMutation = useUpsertScoringRule();
  const evaluateMutation = useEvaluateScoringRule();

  const [name, setName] = useState("Tenant override");
  const [targetType, setTargetType] = useState<ScoringTargetType>("company");
  const [weights, setWeights] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      Object.entries(PLATFORM_DEFAULT_DIMENSION_WEIGHTS).map(([k, v]) => [k, String(v)])
    )
  );
  const [boostField, setBoostField] = useState("segment");
  const [boostOp, setBoostOp] = useState<ScoringBoostOp>("eq");
  const [boostValue, setBoostValue] = useState("enterprise");
  const [boostDelta, setBoostDelta] = useState("5");
  const [includeBoost, setIncludeBoost] = useState(false);

  const [evalScores, setEvalScores] = useState(
    () =>
      `{\n  "buying_intent": 80,\n  "engagement": 70,\n  "fit": 60,\n  "urgency": 50,\n  "relationship": 40,\n  "market_signal": 30\n}`
  );
  const [evalAttrs, setEvalAttrs] = useState(`{\n  "segment": "enterprise"\n}`);
  const [evalRuleId, setEvalRuleId] = useState("");

  const parsedWeights = useMemo(() => {
    const out: Record<string, number> = {};
    for (const dim of SCORING_DIMENSIONS) {
      const raw = weights[dim];
      if (raw == null || String(raw).trim() === "") continue;
      const n = Number(raw);
      if (!Number.isFinite(n)) continue;
      out[dim] = n;
    }
    return out;
  }, [weights]);

  return (
    <div className="space-y-4" data-testid="scoring-rules-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="scoring-rules-honesty"
      >
        {SCORING_RULES_HONESTY} Non-goals: {SCORING_RULES_NON_GOALS.join("; ")}. Not Production GO /
        RAG GO.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="scoring-rules-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh rules"}
        </Button>
        <span className="text-sm text-[var(--text-muted)]" data-testid="scoring-rules-count">
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">{getApiError(listQuery.error)}</span>
          ) : (
            <>{listQuery.data?.length ?? 0} rule(s)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="scoring-rules-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No tenant scoring rules yet. Upsert one below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((rule) => (
            <li key={rule.id} className="px-3 py-2 text-sm" data-testid="scoring-rules-row">
              <span className="font-medium">{rule.name}</span> · {rule.target_type} ·{" "}
              {rule.active ? "active" : "inactive"}
              <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                {rule.id} · v{rule.schema_version} · weights{" "}
                {JSON.stringify(rule.dimension_weights)}
              </span>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="scoring-rules-upsert-form"
        onSubmit={(e) => {
          e.preventDefault();
          const boosts = includeBoost
            ? [
                {
                  field: boostField.trim(),
                  op: boostOp,
                  value: boostValue,
                  delta: Number(boostDelta) || 0,
                },
              ]
            : [];
          upsertMutation.mutate(
            {
              name: name.trim(),
              target_type: targetType,
              dimension_weights: parsedWeights,
              boosts,
              active: true,
            },
            {
              onSuccess: (row) => {
                toast({
                  variant: "success",
                  title: "Scoring rule saved",
                  description: `${row.name} (${row.id})`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Upsert failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">Upsert rule (tip POST)</h2>
        <Input
          label="name"
          data-testid="scoring-rules-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div>
          <label className="block text-xs text-[var(--text-muted)]">target_type</label>
          <select
            data-testid="scoring-rules-target-type"
            className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={targetType}
            onChange={(e) => setTargetType(e.target.value as ScoringTargetType)}
          >
            {SCORING_TARGET_TYPES.map((tt) => (
              <option key={tt} value={tt}>
                {tt}
              </option>
            ))}
          </select>
        </div>
        <div
          className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
          data-testid="scoring-rules-weights"
        >
          {SCORING_DIMENSIONS.map((dim) => (
            <Input
              key={dim}
              label={dim}
              data-testid={`scoring-rules-weight-${dim}`}
              type="number"
              step="0.01"
              min="0"
              value={weights[dim] ?? ""}
              onChange={(e) => setWeights((prev) => ({ ...prev, [dim]: e.target.value }))}
            />
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            data-testid="scoring-rules-include-boost"
            checked={includeBoost}
            onChange={(e) => setIncludeBoost(e.target.checked)}
          />
          Include attribute boost
        </label>
        {includeBoost ? (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <Input
              label="boost.field"
              data-testid="scoring-rules-boost-field"
              value={boostField}
              onChange={(e) => setBoostField(e.target.value)}
            />
            <div>
              <label className="block text-xs text-[var(--text-muted)]">boost.op</label>
              <select
                data-testid="scoring-rules-boost-op"
                className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={boostOp}
                onChange={(e) => setBoostOp(e.target.value as ScoringBoostOp)}
              >
                {SCORING_BOOST_OPS.map((op) => (
                  <option key={op} value={op}>
                    {op}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="boost.value"
              data-testid="scoring-rules-boost-value"
              value={boostValue}
              onChange={(e) => setBoostValue(e.target.value)}
            />
            <Input
              label="boost.delta"
              data-testid="scoring-rules-boost-delta"
              type="number"
              value={boostDelta}
              onChange={(e) => setBoostDelta(e.target.value)}
            />
          </div>
        ) : null}
        <Button
          type="submit"
          data-testid="scoring-rules-submit"
          disabled={upsertMutation.isPending || !name.trim()}
        >
          {upsertMutation.isPending ? "Saving…" : "Save scoring rule"}
        </Button>
      </form>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="scoring-rules-evaluate-form"
        onSubmit={(e) => {
          e.preventDefault();
          let dimension_scores: Record<string, number> = {};
          let attributes: Record<string, unknown> = {};
          try {
            dimension_scores = JSON.parse(evalScores) as Record<string, number>;
          } catch {
            toast({
              variant: "error",
              title: "Invalid dimension_scores JSON",
            });
            return;
          }
          try {
            attributes = JSON.parse(evalAttrs) as Record<string, unknown>;
          } catch {
            toast({
              variant: "error",
              title: "Invalid attributes JSON",
            });
            return;
          }
          evaluateMutation.mutate(
            {
              target_type: targetType,
              dimension_scores,
              attributes,
              rule_id: evalRuleId.trim() || null,
            },
            {
              onSuccess: (row) => {
                toast({
                  variant: "success",
                  title: `Score ${row.score}`,
                  description: `${row.source}${
                    row.fallback_used ? ` · fallback: ${row.fallback_reason ?? "yes"}` : ""
                  }`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Evaluate failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Evaluate (tip POST …/evaluate)
        </h2>
        <Input
          label="rule_id (optional — leave empty for active tenant rule)"
          data-testid="scoring-rules-eval-rule-id"
          value={evalRuleId}
          onChange={(e) => setEvalRuleId(e.target.value)}
        />
        <div>
          <label className="block text-xs text-[var(--text-muted)]">dimension_scores (JSON)</label>
          <textarea
            data-testid="scoring-rules-eval-scores"
            className="min-h-[120px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs"
            value={evalScores}
            onChange={(e) => setEvalScores(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs text-[var(--text-muted)]">attributes (JSON)</label>
          <textarea
            data-testid="scoring-rules-eval-attrs"
            className="min-h-[80px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs"
            value={evalAttrs}
            onChange={(e) => setEvalAttrs(e.target.value)}
          />
        </div>
        <Button
          type="submit"
          data-testid="scoring-rules-evaluate"
          disabled={evaluateMutation.isPending}
        >
          {evaluateMutation.isPending ? "Evaluating…" : "Evaluate score"}
        </Button>
        {evaluateMutation.data ? (
          <pre
            className="overflow-auto rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-[10px] text-[var(--text-muted)]"
            data-testid="scoring-rules-eval-result"
          >
            {JSON.stringify(evaluateMutation.data, null, 2)}
          </pre>
        ) : null}
      </form>
    </div>
  );
}
