/**
 * STORY-06-03 / FE-S06-03b — parse UsageMeter quota gate payloads.
 * Honest upgrade / reduce-usage messaging. Not Production GO.
 */

export type QuotaExceededPayload = {
  detail?: string;
  error?: string;
  metric?: string;
  used?: number;
  limit?: number;
  period?: string | null;
  plan_id?: string | null;
  tier?: string | null;
};

export const QUOTA_EXCEEDED_EVENT = "salesos:quota-exceeded";

const QUOTA_METRICS = new Set([
  "seats",
  "connectors",
  "storage_mb",
  "ai_tokens",
]);

export function isQuotaExceededPayload(
  data: unknown,
): data is QuotaExceededPayload {
  if (!data || typeof data !== "object") return false;
  const d = data as QuotaExceededPayload;
  if (d.error !== "quota_exceeded") return false;
  if (typeof d.metric !== "string" || !QUOTA_METRICS.has(d.metric)) {
    return false;
  }
  const detail = typeof d.detail === "string" ? d.detail : "";
  return (
    detail.toLowerCase().includes("quota exceeded") ||
    detail.toLowerCase().includes("upgrade plan")
  );
}

export function formatQuotaExceededMessage(
  payload: QuotaExceededPayload,
): string {
  const metric = payload.metric || "unknown";
  const used =
    typeof payload.used === "number" && Number.isFinite(payload.used)
      ? String(payload.used)
      : "n/a";
  const limit =
    typeof payload.limit === "number" && Number.isFinite(payload.limit)
      ? String(payload.limit)
      : "n/a";
  const tier = payload.tier || "unknown-tier";
  const plan = payload.plan_id || "unset";
  const period = payload.period ? ` \u00b7 period=${payload.period}` : "";
  const rateNote =
    metric === "ai_tokens"
      ? " Token gates return HTTP 429; seats/connectors/storage return 403."
      : " Capacity gates return HTTP 403.";
  return (
    `Plan quota exceeded: ${metric} (used ${used} / limit ${limit}).` +
    ` Current tier=${tier} \u00b7 plan_id=${plan}${period}.` +
    ` Upgrade plan or reduce usage.` +
    rateNote +
    ` Not Production GO.`
  );
}

export function getQuotaExceededFromError(
  err: unknown,
): QuotaExceededPayload | null {
  if (typeof err !== "object" || err === null || !("response" in err)) {
    return null;
  }
  const response = (err as { response?: { status?: number; data?: unknown } })
    .response;
  if (response?.status !== 403 && response?.status !== 429) return null;
  return isQuotaExceededPayload(response.data) ? response.data : null;
}
