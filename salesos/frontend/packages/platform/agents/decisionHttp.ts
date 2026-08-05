/**
 * Decision Center HTTP bridge for agent tools/orchestrator.
 *
 * Does NOT use the @salesos/decision-platform STUB (throws on evaluate).
 * Prefer this path so agents do not invent live Decision Engine capability.
 * See PROD-W6-001 / AI_HONESTY.md — not Production GO / not AI-native GA.
 */

import type {
  DecisionContext,
  DecisionResult,
} from "@salesos/decision-platform";

export type DecisionEvaluateFn = (
  context: DecisionContext,
) => Promise<DecisionResult>;

function toApiBody(context: DecisionContext) {
  return {
    tenant_id: context.tenantId,
    actor_id: context.actorId,
    entity_id: context.entityId,
    entity_type: context.entityType,
    opportunity_id: context.opportunityId,
    company_id: context.companyId,
    signal_id: context.signalId,
    metadata: context.metadata,
  };
}

async function defaultHttpEvaluate(
  context: DecisionContext,
): Promise<DecisionResult> {
  const body = toApiBody(context);
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (body.tenant_id) {
    headers["X-Tenant-Id"] = String(body.tenant_id);
  }

  const res = await fetch("/api/v1/decision/evaluate", {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = "";
    try {
      detail = await res.text();
    } catch {
      detail = "";
    }
    throw new Error(
      `Decision Center evaluate failed: HTTP ${res.status}${
        detail ? ` ${detail.slice(0, 200)}` : ""
      }`,
    );
  }

  return (await res.json()) as DecisionResult;
}

let evaluateImpl: DecisionEvaluateFn = defaultHttpEvaluate;

/** Inject evaluator for tests; pass null to restore HTTP default. */
export function setDecisionEvaluate(fn: DecisionEvaluateFn | null): void {
  evaluateImpl = fn ?? defaultHttpEvaluate;
}

export function evaluateDecision(
  context: DecisionContext,
): Promise<DecisionResult> {
  return evaluateImpl(context);
}
