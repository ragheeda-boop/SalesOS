"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { companyKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useLogin() {
  return useMutation({
    mutationFn: async ({
      email,
      password,
    }: {
      email: string;
      password: string;
    }) => {
      const response = await api.post("/api/v1/identity/login", { email, password });
      const { access_token, refresh_token, tenant_id } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      if (tenant_id) localStorage.setItem("tenant_id", tenant_id);
      return response.data;
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async ({
      email,
      password,
      fullName,
    }: {
      email: string;
      password: string;
      fullName: string;
    }) => {
      const response = await api.post("/api/v1/identity/register", {
        email,
        password,
        full_name: fullName,
      });
      const { access_token, refresh_token, tenant_id } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      if (tenant_id) localStorage.setItem("tenant_id", tenant_id);
      return response.data;
    },
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      name_ar: string;
      cr_number: string;
      name_en?: string;
      status?: string;
      city?: string;
      region?: string;
    }) => {
      const response = await api.post("/api/v1/companies", data, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: {
      id: string;
      name_ar?: string;
      name_en?: string;
      status?: string;
      city?: string;
      region?: string;
    }) => {
      const response = await api.patch(`/api/v1/companies/${id}`, data, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}
