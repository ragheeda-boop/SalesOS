import {
  REFRESH_TOKEN_KEY,
  clearAuthTokens,
  persistAuthTokens,
} from "@/lib/auth/session";
import api from "./client";
import type { UserProfile } from "./types";

export interface TokenBundle {
  access_token: string;
  refresh_token: string;
  tenant_id?: string;
  token_type?: string;
  expires_in?: number;
}

export interface LogoutResponse {
  message: string;
  sessions_revoked: number;
}

export async function login(email: string, password: string) {
  const response = await api.post("/api/v1/identity/login", {
    email,
    password,
  });
  const { access_token, refresh_token, tenant_id } = response.data;
  persistAuthTokens({ access_token, refresh_token, tenant_id });
  return response.data;
}

export async function register(
  email: string,
  password: string,
  fullName: string,
) {
  const response = await api.post("/api/v1/identity/register", {
    email,
    password,
    full_name: fullName,
  });
  const { access_token, refresh_token, tenant_id } = response.data;
  persistAuthTokens({ access_token, refresh_token, tenant_id });
  return response.data;
}

export async function getCurrentUser(): Promise<UserProfile> {
  const response = await api.get("/api/v1/identity/users/me");
  return response.data;
}

export async function changePassword(
  current_password: string,
  new_password: string,
): Promise<{ message: string }> {
  const response = await api.post("/api/v1/identity/change-password", {
    current_password,
    new_password,
  });
  return response.data;
}

/**
 * FE-SEC-04 — Prefer BE httponly refresh cookie (empty body).
 * Falls back to localStorage refresh_token so http/Secure-drop does not break auth.
 */
export async function refreshSession(): Promise<TokenBundle> {
  try {
    const cookieFirst = await api.post<TokenBundle>(
      "/api/v1/identity/refresh",
      {},
    );
    const data = cookieFirst.data;
    persistAuthTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      tenant_id: data.tenant_id,
    });
    return data;
  } catch (err) {
    const lsRefresh =
      typeof window !== "undefined"
        ? localStorage.getItem(REFRESH_TOKEN_KEY)
        : null;
    if (!lsRefresh) throw err;
    const bodyFallback = await api.post<TokenBundle>(
      "/api/v1/identity/refresh",
      { refresh_token: lsRefresh },
    );
    const data = bodyFallback.data;
    persistAuthTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      tenant_id: data.tenant_id,
    });
    return data;
  }
}

/**
 * FE-SEC-03 — Tip POST /api/v1/identity/logout (Bearer + CSRF).
 * Always clears local session afterward even if BE revoke fails.
 */
export async function logoutSession(options?: {
  all_sessions?: boolean;
  session_id?: string;
}): Promise<LogoutResponse | null> {
  const refresh =
    typeof window !== "undefined"
      ? localStorage.getItem(REFRESH_TOKEN_KEY)
      : null;
  try {
    const response = await api.post<LogoutResponse>("/api/v1/identity/logout", {
      refresh_token: refresh || undefined,
      session_id: options?.session_id,
      all_sessions: options?.all_sessions ?? false,
    });
    return response.data;
  } catch {
    return null;
  } finally {
    clearAuthTokens();
  }
}
