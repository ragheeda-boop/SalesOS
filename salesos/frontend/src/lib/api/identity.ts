import api from "./client";
import type { UserProfile } from "./types";

export async function login(email: string, password: string) {
  const response = await api.post("/api/v1/identity/login", {
    email,
    password,
  });
  const { access_token, refresh_token } = response.data;
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
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
  const { access_token, refresh_token } = response.data;
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
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
