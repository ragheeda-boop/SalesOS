/**
 * FE-SEC-02 — flag helper defaults OFF (no invent flags-on field PASS).
 */
import { isHttpOnlyAccessCookieEnabled } from "../httpOnlyAccessCookie";

describe("isHttpOnlyAccessCookieEnabled", () => {
  const originalPublic = process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;
  const originalServer = process.env.FEATURE_HTTPONLY_ACCESS_COOKIE;

  afterEach(() => {
    if (originalPublic === undefined) {
      delete process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;
    } else {
      process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = originalPublic;
    }
    if (originalServer === undefined) {
      delete process.env.FEATURE_HTTPONLY_ACCESS_COOKIE;
    } else {
      process.env.FEATURE_HTTPONLY_ACCESS_COOKIE = originalServer;
    }
  });

  it("defaults OFF when unset", () => {
    delete process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;
    delete process.env.FEATURE_HTTPONLY_ACCESS_COOKIE;
    expect(isHttpOnlyAccessCookieEnabled()).toBe(false);
  });

  it("is OFF for falsey string values", () => {
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = "false";
    delete process.env.FEATURE_HTTPONLY_ACCESS_COOKIE;
    expect(isHttpOnlyAccessCookieEnabled()).toBe(false);
  });

  it("is ON only for exact true (public or server)", () => {
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE = "true";
    expect(isHttpOnlyAccessCookieEnabled()).toBe(true);
    delete process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE;
    process.env.FEATURE_HTTPONLY_ACCESS_COOKIE = "true";
    expect(isHttpOnlyAccessCookieEnabled()).toBe(true);
  });
});
