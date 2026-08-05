/**
 * Identity logout / refresh API — FE-SEC-03 / FE-SEC-04.
 */
import { logoutSession, refreshSession } from "../identity";

jest.mock("../../auth/session", () => ({
  REFRESH_TOKEN_KEY: "refresh_token",
  clearAuthTokens: jest.fn(),
  persistAuthTokens: jest.fn(),
}));

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
  },
}));

import api from "../client";
import { clearAuthTokens, persistAuthTokens } from "../../auth/session";

const mockedApi = api as unknown as { post: jest.Mock };

describe("identity logout/refresh — FE-SEC-03/04", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it("refreshSession prefers empty-body cookie path", async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: {
        access_token: "a2",
        refresh_token: "r2",
        tenant_id: "t1",
      },
    });
    const data = await refreshSession();
    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/identity/refresh", {});
    expect(persistAuthTokens).toHaveBeenCalledWith({
      access_token: "a2",
      refresh_token: "r2",
      tenant_id: "t1",
    });
    expect(data.access_token).toBe("a2");
  });

  it("refreshSession falls back to LS body refresh_token", async () => {
    localStorage.setItem("refresh_token", "rt-ls");
    mockedApi.post.mockRejectedValueOnce(new Error("no cookie")).mockResolvedValueOnce({
      data: {
        access_token: "a3",
        refresh_token: "r3",
        tenant_id: "t1",
      },
    });
    await refreshSession();
    expect(mockedApi.post).toHaveBeenNthCalledWith(2, "/api/v1/identity/refresh", {
      refresh_token: "rt-ls",
    });
  });

  it("logoutSession posts revoke then clears local tokens", async () => {
    localStorage.setItem("refresh_token", "rt-1");
    mockedApi.post.mockResolvedValueOnce({
      data: { message: "Logged out successfully", sessions_revoked: 1 },
    });
    const result = await logoutSession();
    expect(mockedApi.post).toHaveBeenCalledWith("/api/v1/identity/logout", {
      refresh_token: "rt-1",
      session_id: undefined,
      all_sessions: false,
    });
    expect(result?.sessions_revoked).toBe(1);
    expect(clearAuthTokens).toHaveBeenCalled();
  });

  it("logoutSession still clears when BE fails", async () => {
    mockedApi.post.mockRejectedValueOnce(new Error("network"));
    const result = await logoutSession();
    expect(result).toBeNull();
    expect(clearAuthTokens).toHaveBeenCalled();
  });
});
