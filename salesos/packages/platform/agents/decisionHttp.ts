import type {
  DecisionContext,
  DecisionResult,
} from "@salesos/decision-platform";

export type DecisionEvaluator = (
  context: DecisionContext,
) => Promise<DecisionResult>;

export interface DecisionHttpConfig {
  baseUrl: string;
  bearerToken?: string;
  fetcher?: DecisionFetch;
}

export interface DecisionFetchResponse {
  ok: boolean;
  status: number;
  statusText: string;
  json(): Promise<unknown>;
}

export type DecisionFetch = (
  input: string,
  init: {
    method: "POST";
    headers: Record<string, string>;
    body: string;
  },
) => Promise<DecisionFetchResponse>;

let injectedEvaluator: DecisionEvaluator | null = null;
let httpConfig: DecisionHttpConfig | null = null;

/**
 * Inject a deterministic evaluator for tests and local lab orchestration.
 * Passing null restores the real HTTP path.
 */
export function setDecisionEvaluate(evaluator: DecisionEvaluator | null): void {
  injectedEvaluator = evaluator;
}

/** Configure the explicit Decision Platform HTTP transport for a lab/runtime host. */
export function configureDecisionHttp(config: DecisionHttpConfig | null): void {
  httpConfig = config;
}

function defaultFetch(): DecisionFetch {
  const candidate = (globalThis as { fetch?: DecisionFetch }).fetch;
  if (!candidate) {
    throw new Error(
      "Decision HTTP transport is unavailable: provide a fetcher or a runtime with fetch",
    );
  }
  return candidate;
}

function normalizeBaseUrl(baseUrl: string): string {
  const normalized = baseUrl.trim().replace(/\/+$/, "");
  if (!normalized) throw new Error("Decision HTTP baseUrl must not be empty");
  return normalized;
}

/**
 * Evaluate through the governed HTTP boundary when no test evaluator is injected.
 * The endpoint is the alternate Decision Platform evaluation API; durable governed
 * ledger writes remain owned by Decision Center on /api/v1/decisions*.
 */
export async function evaluateDecision(
  context: DecisionContext,
): Promise<DecisionResult> {
  if (injectedEvaluator) return injectedEvaluator(context);
  if (!httpConfig) {
    throw new Error(
      "Decision HTTP client is not configured: call configureDecisionHttp() or inject setDecisionEvaluate()",
    );
  }

  const fetcher = httpConfig.fetcher ?? defaultFetch();
  const response = await fetcher(
    `${normalizeBaseUrl(httpConfig.baseUrl)}/api/v1/decision/evaluate`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Tenant-Id": context.tenantId,
        ...(httpConfig.bearerToken
          ? { Authorization: `Bearer ${httpConfig.bearerToken}` }
          : {}),
      },
      body: JSON.stringify(context),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Decision HTTP evaluation failed (${response.status} ${response.statusText})`,
    );
  }

  return (await response.json()) as DecisionResult;
}
