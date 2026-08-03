/**
 * FE-SEC-02 — httpOnly access cookie vertical slice (flag OFF by default).
 * Cookie name must match BE ACCESS_COOKIE when feature_httponly_access_cookie=true.
 * Next middleware can read httpOnly cookies; document.cookie cannot.
 */

export const HTTPONLY_ACCESS_COOKIE = "salesos_access";

/** Mirror BE `feature_httponly_access_cookie` / NEXT_PUBLIC kill-switch. Default OFF. */
export function isHttpOnlyAccessCookieEnabled(): boolean {
  return (
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE === "true" ||
    process.env.FEATURE_HTTPONLY_ACCESS_COOKIE === "true"
  );
}
