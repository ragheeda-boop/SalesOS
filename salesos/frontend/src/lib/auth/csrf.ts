/**
 * Tip CSRF double-submit helpers (STORY-14-04 FE support).
 * BE: GET /api/v1/identity/csrf-token sets csrf_token cookie;
 * mutating methods require matching X-CSRF-Token.
 * Does not weaken auth. feature_ai_copilot unchanged.
 */

export const CSRF_COOKIE = "csrf_token";
export const CSRF_HEADER = "X-CSRF-Token";
export const CSRF_TOKEN_PATH = "/api/v1/identity/csrf-token";

const CSRF_EXEMPT_PATH_SUFFIXES = [
  "/api/v1/identity/login",
  "/api/v1/identity/owner/login",
  "/api/v1/identity/register",
  "/api/v1/identity/forgot-password",
  "/api/v1/identity/reset-password",
  "/api/v1/identity/refresh",
  CSRF_TOKEN_PATH,
  "/api/v1/billing/stripe/webhook",
] as const;

const MUTATING_METHODS = new Set(["post", "put", "patch", "delete"]);

export function isMutatingMethod(method?: string): boolean {
  return MUTATING_METHODS.has(String(method || "get").toLowerCase());
}

export function isCsrfExemptUrl(url?: string): boolean {
  if (!url) return false;
  const path = url.split("?")[0] || "";
  return CSRF_EXEMPT_PATH_SUFFIXES.some((suffix) => path === suffix || path.endsWith(suffix));
}

export function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const parts = document.cookie.split("; ");
  for (const part of parts) {
    if (part.startsWith(`${name}=`)) {
      const raw = part.slice(name.length + 1);
      try {
        return decodeURIComponent(raw);
      } catch {
        return raw;
      }
    }
  }
  return null;
}

/** Mirror BE csrf cookie when Secure Set-Cookie is dropped (e.g. http local). */
export function mirrorCsrfCookie(token: string): void {
  if (typeof document === "undefined" || !token) return;
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${CSRF_COOKIE}=${encodeURIComponent(token)}; path=/; SameSite=Strict; max-age=86400${secure}`;
}

export function clearCachedCsrfCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${CSRF_COOKIE}=; path=/; max-age=0; SameSite=Strict`;
}

export function isCsrfFailurePayload(data: unknown): boolean {
  const detail =
    data && typeof data === "object" && "detail" in data
      ? String((data as { detail?: unknown }).detail ?? "")
      : "";
  return /csrf/i.test(detail);
}
