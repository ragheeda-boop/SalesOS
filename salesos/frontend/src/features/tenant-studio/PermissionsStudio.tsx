"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCheckPermissionsCeiling,
  useCustomRoles,
  usePermissionsCatalog,
  usePermissionsCeiling,
  useSetPermissionsCeiling,
  useUpsertCustomRole,
} from "@/lib/hooks/permissionsStudioQueries";
import type { StudioPlanTier } from "@/lib/api/types/tenantStudio";
import { STUDIO_PLAN_TIERS } from "@/lib/api/types/tenantStudio";
import {
  PERMISSIONS_STUDIO_HONESTY,
  PERMISSIONS_STUDIO_NON_GOALS,
} from "@/features/tenant-studio/permissionsStudioHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-06 — Permissions Studio against tip STORY-10-06 HTTP.
 * Custom roles capped at Plan.entitlements. Not Production GO / RAG GO.
 * TenantList untouched. Does not mutate Owner /admin/roles.
 */
export function PermissionsStudio() {
  const { toast } = useToast();
  const catalogQuery = usePermissionsCatalog();
  const ceilingQuery = usePermissionsCeiling();
  const rolesQuery = useCustomRoles();
  const setCeilingMutation = useSetPermissionsCeiling();
  const upsertMutation = useUpsertCustomRole();
  const checkMutation = useCheckPermissionsCeiling();

  const [planTier, setPlanTier] = useState<StudioPlanTier>("starter");
  const [roleName, setRoleName] = useState("Seller");
  const [roleDescription, setRoleDescription] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const selectedKeys = Object.entries(selected)
    .filter(([, on]) => on)
    .map(([k]) => k);

  return (
    <div className="space-y-4" data-testid="permissions-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="permissions-studio-honesty"
      >
        {PERMISSIONS_STUDIO_HONESTY} Non-goals: {PERMISSIONS_STUDIO_NON_GOALS.join("; ")}. Not
        Production GO / RAG GO.
      </p>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-[var(--text-muted)]">plan_tier (ceiling)</label>
          <select
            data-testid="permissions-plan-tier"
            className="rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={planTier}
            onChange={(e) => setPlanTier(e.target.value as StudioPlanTier)}
          >
            {STUDIO_PLAN_TIERS.map((tier) => (
              <option key={tier} value={tier}>
                {tier}
              </option>
            ))}
          </select>
        </div>
        <Button
          data-testid="permissions-set-ceiling"
          disabled={setCeilingMutation.isPending}
          onClick={() => {
            setCeilingMutation.mutate(
              { plan_tier: planTier },
              {
                onSuccess: (row) => {
                  toast({
                    variant: "success",
                    title: "Ceiling set",
                    description: `${row.grantable_permissions?.length ?? 0} grantable`,
                  });
                },
                onError: (err) => {
                  toast({
                    variant: "error",
                    title: "Set ceiling failed",
                    description: getApiError(err),
                  });
                },
              }
            );
          }}
        >
          {setCeilingMutation.isPending ? "Saving…" : "Set ceiling (tip PUT)"}
        </Button>
        <Button
          data-testid="permissions-refresh"
          disabled={catalogQuery.isFetching || ceilingQuery.isFetching || rolesQuery.isFetching}
          onClick={() => {
            void catalogQuery.refetch();
            void ceilingQuery.refetch();
            void rolesQuery.refetch();
          }}
        >
          Refresh
        </Button>
      </div>

      <div
        className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
        data-testid="permissions-ceiling-meta"
      >
        {ceilingQuery.isLoading ? (
          <Spinner className="h-5 w-5" />
        ) : ceilingQuery.isError ? (
          <span className="text-[var(--text-danger)]">{getApiError(ceilingQuery.error)}</span>
        ) : (
          <>
            grantable{" "}
            <span className="font-mono">
              {ceilingQuery.data?.grantable_permissions?.length ?? 0}
            </span>
            {" · "}
            enabled domains{" "}
            <span className="font-mono text-xs">
              {(ceilingQuery.data?.enabled_domains ?? []).join(", ") || "—"}
            </span>
          </>
        )}
      </div>

      <div
        className="rounded border border-[var(--border-default)] p-3"
        data-testid="permissions-catalog"
      >
        <h2 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">
          Catalog (tip GET …/catalog)
        </h2>
        {catalogQuery.isLoading ? (
          <Spinner className="h-5 w-5" />
        ) : catalogQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(catalogQuery.error)}</p>
        ) : (
          <ul className="max-h-64 space-y-1 overflow-auto text-sm">
            {(catalogQuery.data ?? []).map((item) => (
              <li
                key={item.key}
                className="flex items-start gap-2"
                data-testid="permissions-catalog-row"
              >
                <input
                  type="checkbox"
                  data-testid={`permissions-select-${item.key}`}
                  disabled={!item.within_ceiling}
                  checked={!!selected[item.key]}
                  onChange={(e) =>
                    setSelected((prev) => ({
                      ...prev,
                      [item.key]: e.target.checked,
                    }))
                  }
                />
                <span>
                  <span className="font-medium">{item.name}</span>{" "}
                  <span className="font-mono text-xs">({item.key})</span> · {item.domain}
                  {item.within_ceiling ? (
                    <span className="ml-1 text-xs text-emerald-700 dark:text-emerald-300">
                      within ceiling
                    </span>
                  ) : (
                    <span className="ml-1 text-xs text-[var(--text-danger)]">
                      blocked
                      {item.ceiling_reason ? `: ${item.ceiling_reason}` : ""}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="permissions-roles-list"
      >
        {(rolesQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No custom roles yet. Upsert one below (tip POST …/roles).
          </li>
        ) : (
          (rolesQuery.data ?? []).map((role) => (
            <li key={role.id} className="px-3 py-2 text-sm" data-testid="permissions-role-row">
              <span className="font-medium">{role.name}</span>
              <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                {role.id} · {role.permissions.join(", ")}
              </span>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="permissions-upsert-form"
        onSubmit={(e) => {
          e.preventDefault();
          upsertMutation.mutate(
            {
              name: roleName.trim(),
              description: roleDescription.trim(),
              permissions: selectedKeys,
              plan_tier: planTier,
            },
            {
              onSuccess: (row) => {
                toast({
                  variant: "success",
                  title: "Custom role saved",
                  description: `${row.name} (${row.id})`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Upsert blocked / failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Upsert custom role (tip POST …/roles)
        </h2>
        <Input
          label="name"
          data-testid="permissions-role-name"
          value={roleName}
          onChange={(e) => setRoleName(e.target.value)}
        />
        <Input
          label="description"
          data-testid="permissions-role-description"
          value={roleDescription}
          onChange={(e) => setRoleDescription(e.target.value)}
        />
        <p className="text-xs text-[var(--text-muted)]" data-testid="permissions-selected-count">
          {selectedKeys.length} permission(s) selected
        </p>
        <Button
          type="submit"
          data-testid="permissions-role-submit"
          disabled={upsertMutation.isPending || !roleName.trim()}
        >
          {upsertMutation.isPending ? "Saving…" : "Save custom role"}
        </Button>
      </form>

      <div
        className="space-y-2 rounded border border-[var(--border-default)] p-3"
        data-testid="permissions-check-panel"
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Ceiling check (tip POST …/check)
        </h2>
        <Button
          data-testid="permissions-check"
          disabled={checkMutation.isPending || selectedKeys.length === 0}
          onClick={() => {
            checkMutation.mutate(
              { permissions: selectedKeys, plan_tier: planTier },
              {
                onSuccess: (row) => {
                  toast({
                    variant: row.allowed ? "success" : "error",
                    title: row.allowed ? "Within ceiling" : "Rejected",
                    description: row.allowed
                      ? `${row.grantable.length} grantable`
                      : `rejected: ${row.rejected.join(", ")}`,
                  });
                },
                onError: (err) => {
                  toast({
                    variant: "error",
                    title: "Check failed",
                    description: getApiError(err),
                  });
                },
              }
            );
          }}
        >
          {checkMutation.isPending ? "Checking…" : "Check selected"}
        </Button>
        {checkMutation.data ? (
          <pre
            className="overflow-auto rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-[10px] text-[var(--text-muted)]"
            data-testid="permissions-check-result"
          >
            {JSON.stringify(checkMutation.data, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  );
}
