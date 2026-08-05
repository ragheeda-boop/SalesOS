/**
 * STORY-06-02 — parse EntitlementEnforcementMiddleware 403 payloads.
 * Honest upgrade messaging. Not Production GO.
 */

export type EntitlementDeniedPayload = {
  detail?: string;
  domain?: string;
  path_prefix?: string;
  plan_id?: string | null;
  tier?: string | null;
};

export const ENTITLEMENT_DENIED_EVENT = "salesos:entitlement-denied";

export function isEntitlementDeniedPayload(data: unknown): data is EntitlementDeniedPayload {
  if (!data || typeof data !== "object") return false;
  const d = data as EntitlementDeniedPayload;
  const detail = typeof d.detail === "string" ? d.detail : "";
  return (
    typeof d.domain === "string" &&
    d.domain.startsWith("DOM-") &&
    (detail.includes("Plan entitlement required") || detail.toLowerCase().includes("upgrade plan"))
  );
}

export function formatEntitlementDeniedMessage(payload: EntitlementDeniedPayload): string {
  const domain = payload.domain || "unknown-domain";
  const tier = payload.tier || "unknown-tier";
  const prefix = payload.path_prefix || "gated-path";
  const plan = payload.plan_id || "unset";
  return (
    `Plan entitlement denied for ${domain} (path ${prefix}). ` +
    `Current tier=${tier} · plan_id=${plan}. ` +
    `Upgrade to a plan that enables this domain, or ask Owner to edit Plan.entitlements. ` +
    `Not Production GO.`
  );
}

export function getEntitlementDeniedFromError(err: unknown): EntitlementDeniedPayload | null {
  if (typeof err !== "object" || err === null || !("response" in err)) {
    return null;
  }
  const response = (err as { response?: { status?: number; data?: unknown } }).response;
  if (response?.status !== 403) return null;
  return isEntitlementDeniedPayload(response.data) ? response.data : null;
}
