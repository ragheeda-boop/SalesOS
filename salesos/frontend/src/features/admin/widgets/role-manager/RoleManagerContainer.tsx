"use client"

import { useState, useCallback } from "react"
import { RoleManagerView } from "./RoleManagerView"
import {
  useAdminRoles, useAdminPermissions,
  useCreateAdminRole, useDeleteAdminRole,
} from "@/lib/hooks/adminQueries"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { updateAdminRole } from "@/lib/api"
import { adminKeys } from "@/lib/queryKeys"

export function RoleManagerWidget() {
  const { data: roles, isLoading: rolesLoading, refetch: refetchRoles } = useAdminRoles()
  const { data: permissions, isLoading: permsLoading } = useAdminPermissions()
  const qc = useQueryClient()
  const createMutation = useCreateAdminRole()
  const deleteMutation = useDeleteAdminRole()

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string; permissions?: string[] } }) =>
      updateAdminRole(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: adminKeys.roles() }) },
  })

  const handleCreate = useCallback(async (data: { name: string; description?: string; permissions: string[] }) => {
    await createMutation.mutateAsync(data)
  }, [createMutation])

  const handleUpdate = useCallback(async (id: string, data: { name?: string; description?: string; permissions?: string[] }) => {
    await updateMutation.mutateAsync({ id, data })
  }, [updateMutation])

  const handleDelete = useCallback(async (id: string) => {
    await deleteMutation.mutateAsync(id)
  }, [deleteMutation])

  return (
    <RoleManagerView
      roles={(roles ?? []).filter((r) => !r.is_system)}
      permissions={permissions ?? []}
      loading={rolesLoading || permsLoading}
      onRefresh={refetchRoles}
      onCreateRole={handleCreate}
      onUpdateRole={handleUpdate}
      onDeleteRole={handleDelete}
    />
  )
}
