/**
 * Dual-path tests for FE-SEC-02 flag ON/OFF (flags default OFF in prod).
 */
import {
  ACCESS_TOKEN_KEY,
  clearAuthTokens,
  persistAuthTokens,
  setAccessTokenCookie,
  syncAccessTokenCookieFromStorage,
} from "../session";

function getCookie(name: string): string | undefined {
  const parts = document.cookie.split(";");
  for (const part of parts) {
    const trimmed = part.trim();
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    if (trimmed.slice(0, eq) === name) {
      return decodeURIComponent(trimmed.slice(eq + 1));
    }
  }
  return undefined;
}

describe("session dual-path — FE-SEC-02", () => {
  const originalPublic = process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;

  afterEach(() => {
    localStorage.clear();
    document.cookie = `${ACCESS_TOKEN_KEY}=; path=/; max-age=0`;
    if (originalPublic === undefined) {
      delete process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;
    } else {
      process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = originalPublic;
    }
  });

  it("flag OFF: mirrors access JWT to document cookie", () => {
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = "false";
    persistAuthTokens({
      access_token: "at-off",
      refresh_token: "rt-off",
      tenant_id: "t1",
    });
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("at-off");
    expect(getCookie(ACCESS_TOKEN_KEY)).toBe("at-off");
  });

  it("flag ON: keeps LS Bearer but skips JS-writable access cookie", () => {
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = "true";
    persistAuthTokens({
      access_token: "at-on",
      refresh_token: "rt-on",
      tenant_id: "t1",
    });
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("at-on");
    expect(getCookie(ACCESS_TOKEN_KEY)).toBeUndefined();
    setAccessTokenCookie("should-not-write");
    expect(getCookie(ACCESS_TOKEN_KEY)).toBeUndefined();
    localStorage.setItem(ACCESS_TOKEN_KEY, "legacy");
    syncAccessTokenCookieFromStorage();
    expect(getCookie(ACCESS_TOKEN_KEY)).toBeUndefined();
    clearAuthTokens();
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
  });
});
