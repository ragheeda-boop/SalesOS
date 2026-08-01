import {
  ACCESS_TOKEN_KEY,
  clearAuthTokens,
  persistAuthTokens,
  readAccessTokenFromCookieHeader,
  syncAccessTokenCookieFromStorage,
} from "../session";

function getCookie(name: string): string | undefined {
  // Avoid non-literal RegExp (CI-19 Wave 5 / ReDoS audit rule).
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

describe("auth session", () => {
  beforeEach(() => {
    localStorage.clear();
    document.cookie = `${ACCESS_TOKEN_KEY}=; path=/; max-age=0`;
  });

  it("persists tokens to localStorage and cookie", () => {
    persistAuthTokens({
      access_token: "at-1",
      refresh_token: "rt-1",
      tenant_id: "t-1",
    });

    expect(localStorage.getItem("access_token")).toBe("at-1");
    expect(localStorage.getItem("refresh_token")).toBe("rt-1");
    expect(localStorage.getItem("tenant_id")).toBe("t-1");
    expect(getCookie("access_token")).toBe("at-1");
  });

  it("clears tokens from localStorage and cookie", () => {
    persistAuthTokens({
      access_token: "at-1",
      refresh_token: "rt-1",
    });
    clearAuthTokens();

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(getCookie("access_token")).toBeUndefined();
  });

  it("syncs cookie from existing localStorage session", () => {
    localStorage.setItem("access_token", "legacy-token");
    syncAccessTokenCookieFromStorage();
    expect(getCookie("access_token")).toBe("legacy-token");
  });

  it("reads access token from cookie header", () => {
    const token = readAccessTokenFromCookieHeader(
      "access_token=abc123; salesos-locale=ar",
    );
    expect(token).toBe("abc123");
  });
});
