/**
 * STORY-07-03 — Owner Console JWT audience helpers.
 * Tenant API: salesos-api. Owner Platform: salesos-owner-platform.
 * Not Production GO. Mint UX still BE follow-up (DEC-093).
 */

export const TENANT_JWT_AUDIENCE = "salesos-api";
export const OWNER_JWT_AUDIENCE = "salesos-owner-platform";

export type JwtAudienceKind = "owner" | "tenant" | "unknown" | "missing";

export function decodeJwtPayload(
  token: string | null | undefined,
): Record<string, unknown> | null {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const normalized = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(normalized);
    const payload = JSON.parse(json) as unknown;
    if (!payload || typeof payload !== "object") return null;
    return payload as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function getJwtAudience(
  token: string | null | undefined,
): string | null {
  const payload = decodeJwtPayload(token);
  const aud = payload?.aud;
  if (typeof aud === "string" && aud.length > 0) return aud;
  if (Array.isArray(aud) && typeof aud[0] === "string") return aud[0];
  return null;
}

export function classifyJwtAudience(
  token: string | null | undefined,
): JwtAudienceKind {
  if (!token) return "missing";
  const aud = getJwtAudience(token);
  if (!aud) return "unknown";
  if (aud === OWNER_JWT_AUDIENCE) return "owner";
  if (aud === TENANT_JWT_AUDIENCE) return "tenant";
  return "unknown";
}

export function isOwnerConsoleAudience(
  token: string | null | undefined,
): boolean {
  return classifyJwtAudience(token) === "owner";
}

export function formatOwnerAudienceHonesty(
  kind: JwtAudienceKind,
  aud?: string | null,
): string {
  if (kind === "owner") {
    return (
      `Owner Console session audience=${OWNER_JWT_AUDIENCE}. ` +
      `Tenant APIs reject this token (EPIC-02 split). Not Production GO.`
    );
  }
  if (kind === "tenant") {
    return (
      `Tenant JWT audience=${TENANT_JWT_AUDIENCE} cannot call /api/v1/admin/* ` +
      `(requires ${OWNER_JWT_AUDIENCE}). Owner login mint remains BE follow-up (DEC-093). ` +
      `Not Production GO.`
    );
  }
  if (kind === "missing") {
    return (
      `No access token in session. Owner Console requires ${OWNER_JWT_AUDIENCE}. ` +
      `Not Production GO.`
    );
  }
  return (
    `Unrecognized JWT audience=${aud || "unset"}. Expected ${OWNER_JWT_AUDIENCE} ` +
    `for Owner Console (STORY-07-03). Not Production GO.`
  );
}
