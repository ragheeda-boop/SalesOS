/**
 * STORY-07-03 / FE-S07-04 — Owner Console JWT audience + host honesty.
 * Tenant API: salesos-api. Owner Platform: salesos-owner-platform.
 * Not Production GO. Mint UX still BE follow-up (DEC-093).
 */

export const TENANT_JWT_AUDIENCE = "salesos-api";
export const OWNER_JWT_AUDIENCE = "salesos-owner-platform";
export const OWNER_CONSOLE_HOST = "owner.salesos.io";

export type JwtAudienceKind = "owner" | "tenant" | "unknown" | "missing";
export type OwnerHostKind = "owner-target" | "local" | "shared-app";

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

export function classifyOwnerHost(
  hostname: string | null | undefined,
): OwnerHostKind {
  if (!hostname) return "shared-app";
  const host = hostname.toLowerCase();
  if (host === OWNER_CONSOLE_HOST || host.endsWith(`.${OWNER_CONSOLE_HOST}`)) {
    return "owner-target";
  }
  if (
    host === "localhost" ||
    host === "127.0.0.1" ||
    host.endsWith(".local") ||
    host === "0.0.0.0"
  ) {
    return "local";
  }
  return "shared-app";
}

export function formatOwnerHostHonesty(
  kind: OwnerHostKind,
  hostname?: string | null,
): string {
  if (kind === "owner-target") {
    return (
      `Host ${hostname || OWNER_CONSOLE_HOST} matches Owner Console target. ` +
      `Separate deploy path only — not a Production GO claim.`
    );
  }
  if (kind === "local") {
    return (
      `Local host ${hostname || "localhost"} — Owner Console MVP routes under /admin. ` +
      `Target host ${OWNER_CONSOLE_HOST} not claimed live. Not Production GO.`
    );
  }
  return (
    `Shared app host ${hostname || "unknown"} — Owner Console shares this Next app today. ` +
    `Target separate host ${OWNER_CONSOLE_HOST} is not claimed live. Not Production GO.`
  );
}

/** FE-S07-06 — admin API path for owner-audience enforcement UX. */
export const OWNER_AUTH_DENIED_EVENT = "salesos:owner-auth-denied";

export function isAdminApiPath(url: string | null | undefined): boolean {
  if (!url) return false;
  return url.includes("/api/v1/admin");
}

/**
 * Tenant-audience sessions hitting Owner admin APIs should toast honesty
 * instead of clearing the tenant session / bouncing to /login.
 * Expired owner tokens still follow the normal 401 → login path.
 */
export function shouldSurfaceOwnerAudienceDenial(options: {
  status?: number;
  url?: string | null;
  token?: string | null;
}): boolean {
  if (options.status !== 401) return false;
  if (!isAdminApiPath(options.url)) return false;
  return classifyJwtAudience(options.token) === "tenant";
}

export function formatOwnerAuthDeniedMessage(
  kind: JwtAudienceKind = "tenant",
): string {
  if (kind === "tenant") {
    return (
      `Owner admin API rejected tenant JWT (${TENANT_JWT_AUDIENCE}). ` +
      `Requires ${OWNER_JWT_AUDIENCE}. Owner login mint remains DEC-093 follow-up — not invented. ` +
      `Tenant session kept. Not Production GO.`
    );
  }
  return formatOwnerAudienceHonesty(kind);
}
