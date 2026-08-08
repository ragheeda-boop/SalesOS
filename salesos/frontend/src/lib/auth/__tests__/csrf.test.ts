import {
  CSRF_COOKIE,
  CSRF_TOKEN_PATH,
  clearCachedCsrfCookie,
  isCsrfExemptUrl,
  isCsrfFailurePayload,
  isMutatingMethod,
  mirrorCsrfCookie,
  readCookie,
} from "../csrf";

describe("csrf helpers — FE 14-04/14-05 support", () => {
  beforeEach(() => {
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "",
      configurable: true,
    });
  });

  it("classifies mutating methods and exempt URLs", () => {
    expect(isMutatingMethod("POST")).toBe(true);
    expect(isMutatingMethod("get")).toBe(false);
    expect(isCsrfExemptUrl(CSRF_TOKEN_PATH)).toBe(true);
    expect(isCsrfExemptUrl("/api/v1/identity/login")).toBe(true);
    expect(isCsrfExemptUrl("/api/v1/identity/owner/login")).toBe(true);
    expect(isCsrfExemptUrl("/api/v1/studio/ai-policies")).toBe(false);
  });

  it("mirrors csrf cookie write", () => {
    mirrorCsrfCookie("tok-abc");
    expect(document.cookie).toMatch(/csrf_token=/);
    clearCachedCsrfCookie();
  });

  it("detects CSRF failure payloads", () => {
    expect(
      isCsrfFailurePayload({
        detail: "CSRF token missing. Include X-CSRF-Token header.",
      })
    ).toBe(true);
    expect(isCsrfFailurePayload({ detail: "forbidden" })).toBe(false);
  });

  it("readCookie returns null when absent", () => {
    expect(readCookie(CSRF_COOKIE)).toBeNull();
  });
});
