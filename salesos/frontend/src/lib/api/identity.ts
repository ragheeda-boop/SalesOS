import { persistAuthTokens } from "@/lib/auth/session";
import api from "./client";
import type { UserProfile } from "./types";

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
