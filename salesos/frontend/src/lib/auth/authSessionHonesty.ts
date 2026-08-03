/**
 * FE-SEC-02 honesty — httpOnly access cookie vertical slice.
 * Not Production GO. feature_ai_copilot False. Decision STUB unchanged.
 */

export const FE_SEC_02_ACCESS_STORAGE =
  "Access JWT remains in localStorage for axios Bearer (BE verify_token is " +
  "header-only). Default path still mirrors non-httpOnly access_token for " +
  "Next middleware when NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE is unset/false.";

export const FE_SEC_02_REFRESH_MITIGATION =
  "Refresh prefers BE httponly refresh_token cookie via POST /api/v1/identity/refresh {}; " +
  "localStorage refresh_token kept as fallback only (Secure cookie drop on http).";

export const FE_SEC_02_HTTPONLY_SLICE =
  "Vertical slice (flag OFF by default): BE feature_httponly_access_cookie sets " +
  "httpOnly salesos_access on login/register/refresh; FE middleware dual-reads " +
  "salesos_access then legacy access_token; when FE flag ON, skip JS-writable " +
  "access cookie mirror. TokenResponse body unchanged. verify_token still Bearer-only.";

export const FE_SEC_02_PROPOSED_NEXT =
  "Proposed follow-on: enable flags on https tip after dual-read field verify; " +
  "optional Bearer-or-cookie verify_token with CSRF for cookie-auth mutations; " +
  "then drop LS access. Do not enable feature_ai_copilot.";
