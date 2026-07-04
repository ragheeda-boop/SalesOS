"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  searchContacts,
  getContact,
  createContact,
  updateContact,
  deleteContact,
  type ContactSearchParams,
  type ContactCreateRequest,
  type ContactUpdateRequest,
  type PaginatedResponse,
  type Contact,
} from "@/lib/api";
import { contactKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useContactSearch(params: ContactSearchParams) {
  return useQuery<PaginatedResponse<Contact>>({
    queryKey: contactKeys.list(params as Record<string, unknown>),
    queryFn: () => searchContacts(params, getTenantId()),
    staleTime: 10_000,
  });
}

export function useContact(id: string) {
  return useQuery<Contact>({
    queryKey: contactKeys.detail(id),
    queryFn: () => getContact(id, getTenantId()),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ContactCreateRequest) => {
      return createContact(data, getTenantId());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...data }: { id: string } & ContactUpdateRequest) => {
      return updateContact(id, data, getTenantId());
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useDeleteContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: string }) => {
      return deleteContact(id, getTenantId());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}
