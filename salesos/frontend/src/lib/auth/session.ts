/**
 * Client/server auth session helpers.
 * Mirrors the existing localStorage `access_token` pattern with a cookie
 * so Next.js middleware can gate routes server-side.
 */

export const ACCESS_TOKEN_KEY = "access_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
export const TENANT_ID_KEY = "tenant_id";

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  tenant_id?: string;
};

function getJwtMaxAgeSeconds(token: string): number | null {
  try {
    const payload = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    ) as { exp?: number };
    if (typeof payload.exp !== "number") return null;
    const seconds = payload.exp - Math.floor(Date.now() / 1000);
    return seconds > 0 ? seconds : null;
  } catch {
    return null;
  }
}

export function setAccessTokenCookie(token: string): void {
  if (typeof document === "undefined") return;
  const maxAge = getJwtMaxAgeSeconds(token) ?? 60 * 60 * 24 * 7;
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${ACCESS_TOKEN_KEY}=${encodeURIComponent(token)}; path=/; SameSite=Lax; max-age=${maxAge}${secure}`;
}

export function clearAccessTokenCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${ACCESS_TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

export function persistAuthTokens(tokens: AuthTokens): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  if (tokens.tenant_id) {
    localStorage.setItem(TENANT_ID_KEY, tokens.tenant_id);
  }
  setAccessTokenCookie(tokens.access_token);
}

export function clearAuthTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TENANT_ID_KEY);
  clearAccessTokenCookie();
}

/** Bridge pre-middleware sessions: localStorage token → cookie for edge gating. */
export function syncAccessTokenCookieFromStorage(): void {
  if (typeof window === "undefined") return;
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    setAccessTokenCookie(token);
  }
}

export function readAccessTokenFromCookieHeader(
  cookieHeader: string | null | undefined,
): string | null {
  if (!cookieHeader) return null;
  const parts = cookieHeader.split(";");
  for (const part of parts) {
    const [rawName, ...rest] = part.trim().split("=");
    if (rawName === ACCESS_TOKEN_KEY) {
      const value = rest.join("=");
      if (!value) return null;
      try {
        return decodeURIComponent(value);
      } catch {
        return value;
      }
    }
  }
  return null;
}

export function hasValidAccessToken(token: string | null | undefined): boolean {
  return typeof token === "string" && token.length > 0;
}
