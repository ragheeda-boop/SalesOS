/**
 * FE-SEC-02 / 03 / 04 honesty — tip identity auth surfaces.
 * Not Production GO. feature_ai_copilot False. Decision STUB unchanged.
 */

export const FE_SEC_02_ACCESS_STORAGE =
  "Access JWT remains in localStorage (+ non-httpOnly access_token cookie) " +
  "so Next.js middleware can gate routes. Full httpOnly access migration needs a " +
  "BFF/edge session pattern — not started this tip (would half-break middleware auth).";

export const FE_SEC_02_REFRESH_MITIGATION =
  "Refresh prefers BE httponly refresh_token cookie via POST /api/v1/identity/refresh {}; " +
  "localStorage refresh_token kept as fallback only (Secure cookie drop on http).";

export const FE_SEC_02_PROPOSED_NEXT =
  "Proposed follow-on: (1) BFF Set-Cookie httpOnly access for middleware-readable " +
  "server session, (2) stop mirroring access JWT to document.cookie, (3) drop LS " +
  "refresh once cookie path proven on https tip. Do not enable feature_ai_copilot.";
