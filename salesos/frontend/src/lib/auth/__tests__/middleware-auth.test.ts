import {
  buildLoginRedirectUrl,
  isProtectedPath,
  isPublicPath,
  readAccessTokenFromRequest,
  shouldRedirectToLogin,
} from "../middleware-auth";
import { ACCESS_TOKEN_KEY } from "../session";
import { HTTPONLY_ACCESS_COOKIE } from "../httpOnlyAccessCookie";

describe("middleware-auth", () => {
  describe("isPublicPath", () => {
    it("allows landing and auth pages", () => {
      expect(isPublicPath("/")).toBe(true);
      expect(isPublicPath("/login")).toBe(true);
      expect(isPublicPath("/register")).toBe(true);
    });

    it("allows api and next internals", () => {
      expect(isPublicPath("/api/v1/identity/login")).toBe(true);
      expect(isPublicPath("/_next/static/chunk.js")).toBe(true);
    });
  });

  describe("isProtectedPath", () => {
    it("protects dashboard routes", () => {
      expect(isProtectedPath("/dashboard")).toBe(true);
      expect(isProtectedPath("/companies/abc")).toBe(true);
      expect(isProtectedPath("/settings")).toBe(true);
    });

    it("protects v3 workspace routes", () => {
      expect(isProtectedPath("/v3")).toBe(true);
      expect(isProtectedPath("/v3/companies")).toBe(true);
    });

    it("does not protect public routes", () => {
      expect(isProtectedPath("/")).toBe(false);
      expect(isProtectedPath("/login")).toBe(false);
      expect(isProtectedPath("/api/v1/identity/login")).toBe(false);
    });
  });

  describe("readAccessTokenFromRequest", () => {
    it("prefers httpOnly salesos_access cookie (FE-SEC-02)", () => {
      const token = readAccessTokenFromRequest({
        cookies: {
          get: (name) => {
            if (name === HTTPONLY_ACCESS_COOKIE) {
              return { value: "httponly-jwt" };
            }
            if (name === ACCESS_TOKEN_KEY) {
              return { value: "legacy-jwt" };
            }
            return undefined;
          },
        },
        headers: { get: () => null },
      });
      expect(token).toBe("httponly-jwt");
    });

    it("reads token from legacy access_token cookie", () => {
      const token = readAccessTokenFromRequest({
        cookies: {
          get: (name) =>
            name === ACCESS_TOKEN_KEY ? { value: "jwt-token" } : undefined,
        },
        headers: { get: () => null },
      });
      expect(token).toBe("jwt-token");
    });

    it("falls back to cookie header", () => {
      const token = readAccessTokenFromRequest({
        cookies: { get: () => undefined },
        headers: {
          get: () => `${ACCESS_TOKEN_KEY}=header-token; other=1`,
        },
      });
      expect(token).toBe("header-token");
    });
  });

  describe("shouldRedirectToLogin", () => {
    it("redirects unauthenticated users on protected routes", () => {
      expect(shouldRedirectToLogin("/dashboard", null)).toBe(true);
      expect(shouldRedirectToLogin("/dashboard", "")).toBe(true);
    });

    it("allows authenticated users and public routes", () => {
      expect(shouldRedirectToLogin("/dashboard", "jwt")).toBe(false);
      expect(shouldRedirectToLogin("/login", null)).toBe(false);
    });
  });

  describe("buildLoginRedirectUrl", () => {
    it("includes callbackUrl for protected path", () => {
      const url = buildLoginRedirectUrl(
        "http://localhost:3000",
        "/companies",
        "?tab=1",
      );
      expect(url.pathname).toBe("/login");
      expect(url.searchParams.get("callbackUrl")).toBe("/companies?tab=1");
    });
  });
});
