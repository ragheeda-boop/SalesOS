import { ACCESS_TOKEN_KEY, hasValidAccessToken, readAccessTokenFromCookieHeader } from "./session";
import { HTTPONLY_ACCESS_COOKIE } from "./httpOnlyAccessCookie";
import { classifyJwtAudience } from "./ownerAudience";

/** Routes that require an authenticated session (dashboard + v3 workspace). */
export const PROTECTED_PREFIXES = [
  "/dashboard",
  "/companies",
  "/employees",
  "/contacts",
  "/opportunities",
  "/activities",
  "/revenue",
  "/pipeline",
  "/forecast",
  "/search",
  "/decisions",
  "/meetings",
  "/graph",
  "/automation",
  "/analytics",
  "/signals",
  "/rules",
  "/monitoring",
  "/customer-success",
  "/settings",
  "/admin",
  "/marketplace",
  "/knowledge",
  "/integrations",
  "/rag",
  "/ai",
  "/copilot",
  "/v3",
] as const;

export const PUBLIC_EXACT_PATHS = new Set(["/", "/login", "/register", "/admin/login"]);

export const PUBLIC_PREFIXES = [
  "/api/",
  "/fe-sec-02/",
  "/_next/",
  "/favicon",
  "/manifest",
  "/icons/",
] as const;

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_EXACT_PATHS.has(pathname)) return true;
  return PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function isProtectedPath(pathname: string): boolean {
  if (isPublicPath(pathname)) return false;
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

function decodeCookieValue(raw: string): string {
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

/**
 * Dual-read for FE-SEC-02 vertical slice:
 * 1) httpOnly `salesos_access` from BE (when flag on)
 * 2) legacy non-httpOnly `access_token` (FE mirror / flag off)
 */
export function readAccessTokenFromRequest(request: {
  cookies: { get: (name: string) => { value: string } | undefined };
  headers: { get: (name: string) => string | null };
}): string | null {
  const httpOnly = request.cookies.get(HTTPONLY_ACCESS_COOKIE)?.value;
  if (httpOnly) {
    return decodeCookieValue(httpOnly);
  }

  const fromCookie = request.cookies.get(ACCESS_TOKEN_KEY)?.value ?? null;
  if (fromCookie) {
    return decodeCookieValue(fromCookie);
  }

  return readAccessTokenFromCookieHeader(request.headers.get("cookie"));
}

export function shouldRedirectToLogin(pathname: string, token: string | null): boolean {
  return isProtectedPath(pathname) && !hasValidAccessToken(token);
}

export function isOwnerConsolePath(pathname: string): boolean {
  return pathname === "/admin" || (pathname.startsWith("/admin/") && pathname !== "/admin/login");
}

/** Tenant/unknown JWT on /admin* → Owner login (DEC-093 mint). */
export function shouldRedirectOwnerConsoleToOwnerLogin(
  pathname: string,
  token: string | null
): boolean {
  if (!isOwnerConsolePath(pathname)) return false;
  if (!hasValidAccessToken(token)) return false;
  return classifyJwtAudience(token) !== "owner";
}

export function buildLoginRedirectUrl(origin: string, pathname: string, search: string): URL {
  const loginPath = isOwnerConsolePath(pathname) ? "/admin/login" : "/login";
  const loginUrl = new URL(loginPath, origin);
  const callback = `${pathname}${search}`;
  if (callback && callback !== "/login" && callback !== "/admin/login") {
    loginUrl.searchParams.set("callbackUrl", callback);
  }
  return loginUrl;
}
