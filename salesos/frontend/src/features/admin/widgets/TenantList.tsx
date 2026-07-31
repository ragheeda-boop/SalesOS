"use client";

import { useState } from "react";
import { Input, Button, Badge, Card, Spinner } from "@salesos/ui";
import { Search, Plus, XCircle, CheckCircle } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import {
  useAdminTenants,
  useCreateAdminTenant,
} from "@/lib/hooks/adminQueries";
import { AdminTenantListItem } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateAdminTenant } from "@/lib/api";
import { adminKeys } from "@/lib/queryKeys";

export function TenantList() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createSlug, setCreateSlug] = useState("");
  const { data: tenants, isLoading } = useAdminTenants({
    search: search || undefined,
    plan: planFilter || undefined,
  });
  const createMutation = useCreateAdminTenant();
  const qc = useQueryClient();

  const updateTenantActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateAdminTenant(id, { is_active }),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: adminKeys.tenants() });
      qc.invalidateQueries({ queryKey: adminKeys.tenantDetail(variables.id) });
    },
  });

  const handleCreate = async () => {
    if (!createName || !createSlug) return;
    await createMutation.mutateAsync({ name: createName, slug: createSlug });
    setShowCreate(false);
    setCreateName("");
    setCreateSlug("");
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t("admin.tenant_list.title")}</h2>
        <Button onClick={() => setShowCreate(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          {t("admin.tenant_list.new_tenant")}
        </Button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
          <Input
            placeholder={t("admin.tenant_list.search_placeholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9"
          />
        </div>
        <select
          value={planFilter}
          onChange={(e) => setPlanFilter(e.target.value)}
          className="border rounded px-3 py-2 text-sm dark:bg-[var(--bg-secondary)] dark:border-[var(--border-default)]"
        >
          <option value="">{t("admin.tenant_list.all_plans")}</option>
          <option value="free">Free</option>
          <option value="starter">Starter</option>
          <option value="growth">Growth</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>

      {showCreate && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">
            {t("admin.tenant_list.new_tenant_title")}
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <Input
              placeholder={t("admin.tenant_list.name_placeholder")}
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
            />
            <Input
              placeholder={t("admin.tenant_list.slug_placeholder")}
              value={createSlug}
              onChange={(e) => setCreateSlug(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {t("admin.tenant_list.create_btn")}
            </Button>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>
              {t("admin.tenant_list.cancel")}
            </Button>
          </div>
        </Card>
      )}

      {isLoading ? (
        <div className="py-20 text-center text-[var(--text-muted)]">
          <Spinner /> {t("admin.tenant_list.loading")}
        </div>
      ) : !tenants?.length ? (
        <Card className="p-6 text-center text-[var(--text-muted)]">
          <Building2Icon className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>{t("admin.tenant_list.no_tenants")}</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-[var(--border-default)] text-right">
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.name")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.slug")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.plan_label")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.users")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.status")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.created_at")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.tenant_list.actions")}
                </th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant: AdminTenantListItem) => (
                <tr
                  key={tenant.id}
                  className="border-b dark:border-[var(--border-default)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-primary)]"
                >
                  <td
                    className="p-2 font-medium"
                    data-label={t("admin.tenant_list.name")}
                  >
                    {tenant.name}
                  </td>
                  <td
                    className="p-2 text-xs text-[var(--text-muted)] font-mono"
                    data-label={t("admin.tenant_list.slug")}
                  >
                    {tenant.slug}
                  </td>
                  <td
                    className="p-2"
                    data-label={t("admin.tenant_list.plan_label")}
                  >
                    <Badge
                      variant={
                        tenant.plan === "enterprise"
                          ? "success"
                          : tenant.plan === "free"
                            ? "default"
                            : "warning"
                      }
                    >
                      {tenant.plan}
                    </Badge>
                  </td>
                  <td className="p-2" data-label={t("admin.tenant_list.users")}>
                    {tenant.user_count}
                  </td>
                  <td
                    className="p-2"
                    data-label={t("admin.tenant_list.status")}
                  >
                    {tenant.is_active ? (
                      <span className="flex items-center gap-1 text-success-600">
                        <CheckCircle className="h-3.5 w-3.5" />{" "}
                        {t("admin.tenant_list.active")}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600">
                        <XCircle className="h-3.5 w-3.5" />{" "}
                        {t("admin.tenant_list.inactive")}
                      </span>
                    )}
                  </td>
                  <td
                    className="p-2 text-xs text-[var(--text-muted)]"
                    data-label={t("admin.tenant_list.created_at")}
                  >
                    {new Date(tenant.created_at).toLocaleDateString("ar-SA")}
                  </td>
                  <td
                    className="p-2"
                    data-label={t("admin.tenant_list.actions")}
                  >
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={updateTenantActive.isPending}
                        onClick={() =>
                          updateTenantActive.mutate({
                            id: tenant.id,
                            is_active: !tenant.is_active,
                          })
                        }
                      >
                        {tenant.is_active
                          ? t("admin.tenant_list.deactivate")
                          : t("admin.tenant_list.activate")}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Building2Icon(props: { className?: string }) {
  return (
    <svg
      {...props}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18M6 22H4m2 0h12m0 0h2M6 7h2m-2 4h2m-2 4h2m6-8h2m-2 4h2m-2 4h2" />
    </svg>
  );
}
