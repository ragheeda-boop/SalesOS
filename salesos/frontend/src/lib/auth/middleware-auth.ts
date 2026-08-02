import {
  ACCESS_TOKEN_KEY,
  hasValidAccessToken,
  readAccessTokenFromCookieHeader,
} from "./session";

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

export const PUBLIC_EXACT_PATHS = new Set(["/", "/login", "/register"]);

export const PUBLIC_PREFIXES = [
  "/api/",
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
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function readAccessTokenFromRequest(request: {
  cookies: { get: (name: string) => { value: string } | undefined };
  headers: { get: (name: string) => string | null };
}): string | null {
  const fromCookie = request.cookies.get(ACCESS_TOKEN_KEY)?.value ?? null;
  if (fromCookie) {
    try {
      return decodeURIComponent(fromCookie);
    } catch {
      return fromCookie;
    }
  }

  return readAccessTokenFromCookieHeader(request.headers.get("cookie"));
}

export function shouldRedirectToLogin(
  pathname: string,
  token: string | null,
): boolean {
  return isProtectedPath(pathname) && !hasValidAccessToken(token);
}

export function buildLoginRedirectUrl(
  origin: string,
  pathname: string,
  search: string,
): URL {
  const loginUrl = new URL("/login", origin);
  const callback = `${pathname}${search}`;
  if (callback && callback !== "/login") {
    loginUrl.searchParams.set("callbackUrl", callback);
  }
  return loginUrl;
}
