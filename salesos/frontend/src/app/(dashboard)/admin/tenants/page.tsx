"use client";

import { useState, useCallback, useMemo } from "react";
import {
  Input,
  Button,
  Badge,
  Spinner,
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useToast,
  Select,
} from "@salesos/ui";
import {
  Search,
  Plus,
  Building2,
  CheckCircle,
  XCircle,
  Trash2,
  Settings,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import {
  useAdminTenants,
  useCreateAdminTenant,
  useUpdateAdminTenant,
  useSuspendAdminTenant,
  useDeleteAdminTenant,
  useHardDeleteAdminTenant,
  useAdminTenantDetail,
  useAdminTenantUsage,
} from "@/lib/hooks/adminQueries";
import type { AdminTenantListItem } from "@/lib/api";
import {
  TenantOwnerPlatformFields,
  fromDateInputValue,
  provisioningStatusLabel,
  provisioningStatusVariant,
  type TenantOwnerPlatformWritePayload,
} from "@/features/admin/widgets/TenantOwnerPlatformFields";
import {
  activityStatusLabel,
  formatProvisionResultDescription,
  formatSuspendResultDescription,
  formatTrialEndsLabel,
  lifecycleStatusDescription,
  sortAdminTenants,
  type TenantSortKey,
  type TrialFilter,
} from "@/features/admin/lib/formatProvisionToast";

const PLAN_OPTIONS = [
  { label: "All Plans", value: "" },
  { label: "Free", value: "free" },
  { label: "Starter", value: "starter" },
  { label: "Growth", value: "growth" },
  { label: "Enterprise", value: "enterprise" },
];

const STATUS_OPTIONS = [
  { label: "All activity", value: "" },
  { label: "Active", value: "active" },
  // API status=suspended → is_active=false (covers soft-delete + suspend)
  { label: "Inactive (is_active=false)", value: "suspended" },
];

const PROVISIONING_FILTER_OPTIONS = [
  { label: "All provisioning", value: "" },
  { label: "Pending", value: "pending" },
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
  { label: "Failed", value: "failed" },
];

const TRIAL_FILTER_OPTIONS: { label: string; value: TrialFilter }[] = [
  { label: "All trials", value: "" },
  { label: "Has trial", value: "has_trial" },
  { label: "Trial expired", value: "expired" },
  { label: "No trial", value: "none" },
];

const SORT_OPTIONS: { label: string; value: TenantSortKey }[] = [
  { label: "Newest first", value: "created_desc" },
  { label: "Oldest first", value: "created_asc" },
  { label: "Name A–Z", value: "name_asc" },
  { label: "Name Z–A", value: "name_desc" },
];

const PLAN_VARIANT: Record<
  string,
  "success" | "warning" | "default" | "danger"
> = {
  enterprise: "success",
  growth: "warning",
  starter: "default",
  free: "default",
};

export default function AdminTenantsPage() {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [planIdFilter, setPlanIdFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [provisioningFilter, setProvisioningFilter] = useState("");
  const [regionFilter, setRegionFilter] = useState("");
  const [residencyFilter, setResidencyFilter] = useState("");
  const [trialFilter, setTrialFilter] = useState<TrialFilter>("");
  const [sortKey, setSortKey] = useState<TenantSortKey>("created_desc");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null,
  );
  const [hardDeleteConfirm, setHardDeleteConfirm] = useState(false);

  const [createForm, setCreateForm] = useState({
    name: "",
    slug: "",
    domain: "",
    admin_email: "",
    plan_id: "",
    region: "",
    data_residency: "",
    trial_ends_at: "",
  });

  // FE-S04-20 — wire Owner Platform filters to GET /admin/tenants query params
  // (tip 0782fa4: plan_id|region|data_residency|provisioning_status|trial + search/plan/status)
  const { data: tenants, isLoading } = useAdminTenants({
    search: search || undefined,
    plan: planFilter || undefined,
    plan_id: planIdFilter.trim() || undefined,
    status: statusFilter || undefined,
    provisioning_status: provisioningFilter || undefined,
    region: regionFilter || undefined,
    data_residency: residencyFilter || undefined,
    trial: trialFilter || undefined,
  });

  const createMutation = useCreateAdminTenant();
  const deleteMutation = useDeleteAdminTenant();
  const hardDeleteMutation = useHardDeleteAdminTenant();

  // Keep current filter values in Select options (server-filtered lists shrink options)
  const regionOptions = useMemo(() => {
    const values = new Set<string>();
    if (regionFilter) values.add(regionFilter);
    for (const t of tenants || []) {
      if (t.region) values.add(t.region);
    }
    return [
      { label: "All regions", value: "" },
      ...Array.from(values)
        .sort()
        .map((v) => ({ label: v, value: v })),
    ];
  }, [tenants, regionFilter]);

  const residencyOptions = useMemo(() => {
    const values = new Set<string>();
    if (residencyFilter) values.add(residencyFilter);
    for (const t of tenants || []) {
      if (t.data_residency) values.add(t.data_residency);
    }
    return [
      { label: "All residency", value: "" },
      ...Array.from(values)
        .sort()
        .map((v) => ({ label: v, value: v })),
    ];
  }, [tenants, residencyFilter]);

  // FE-S04-19 — client sort only; filter/search owned by API (FE-S04-20)
  const filteredTenants = useMemo(() => {
    if (!tenants) return [];
    return sortAdminTenants(tenants, sortKey);
  }, [tenants, sortKey]);

  const totalPages = Math.max(1, Math.ceil(filteredTenants.length / 20));
  const paginatedTenants = filteredTenants.slice((page - 1) * 20, page * 20);

  const handleCreate = useCallback(async () => {
    if (!createForm.name || !createForm.slug) return;
    try {
      const created = await createMutation.mutateAsync({
        name: createForm.name,
        slug: createForm.slug,
        domain: createForm.domain || undefined,
        plan_id: createForm.plan_id || undefined,
        region: createForm.region || undefined,
        data_residency: createForm.data_residency || undefined,
        trial_ends_at: fromDateInputValue(createForm.trial_ends_at),
        admin_email: createForm.admin_email || undefined,
      });
      setShowCreate(false);
      setCreateForm({
        name: "",
        slug: "",
        domain: "",
        admin_email: "",
        plan_id: "",
        region: "",
        data_residency: "",
        trial_ends_at: "",
      });
      toast({
        variant: "success",
        title: "Tenant provisioned",
        description: formatProvisionResultDescription(created),
      });
    } catch {
      toast({
        variant: "error",
        title: "Failed to create tenant",
        description: "An error occurred while creating the tenant.",
      });
    }
  }, [createForm, createMutation, toast]);

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        if (hardDeleteConfirm) {
          // FE-S04-11
          const result = await hardDeleteMutation.mutateAsync({
            id,
            confirm: true,
          });
          setShowDeleteConfirm(null);
          setHardDeleteConfirm(false);
          toast({
            variant: "success",
            title: "Tenant hard-deleted",
            description: `${result.message} · tenant_id=${result.tenant_id}`,
          });
          return;
        }
        // FE-S04-09 — soft-delete honesty
        const result = await deleteMutation.mutateAsync(id);
        setShowDeleteConfirm(null);
        toast({
          variant: "success",
          title: "Tenant soft-deleted",
          description: `${result.message} · is_active=false (recoverable via Activate)`,
        });
      } catch {
        toast({
          variant: "error",
          title: "Failed to delete",
          description: "An error occurred while deleting the tenant.",
        });
      }
    },
    [deleteMutation, hardDeleteMutation, hardDeleteConfirm, toast],
  );

  return (
    <div className="space-y-6" data-testid="admin-tenants-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            Tenant Management
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Provision, configure, suspend, and delete tenants.
          </p>
        </div>
        <Button
          onClick={() => setShowCreate(true)}
          leftIcon={<Plus className="h-4 w-4" />}
          data-testid="admin-tenants-new"
        >
          New Tenant
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search tenants..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          leftIcon={<Search className="h-4 w-4" />}
          className="flex-1 min-w-[200px]"
        />
        <div className="w-44">
          <Select
            options={PLAN_OPTIONS}
            placeholder="Plan"
            value={planFilter}
            onChange={(v) => {
              setPlanFilter(v);
              setPage(1);
            }}
          />
        </div>
        <div className="w-44" data-testid="admin-tenants-plan-id-filter">
          <Input
            placeholder="plan_id…"
            value={planIdFilter}
            onChange={(e) => {
              setPlanIdFilter(e.target.value);
              setPage(1);
            }}
            title="Opaque catalog plan_id (server filter)"
          />
        </div>
        <div className="w-48" data-testid="admin-tenants-status-filter">
          <Select
            options={STATUS_OPTIONS}
            placeholder="Activity"
            value={statusFilter}
            onChange={(v) => {
              setStatusFilter(v);
              setPage(1);
            }}
          />
        </div>
        <div className="w-48" data-testid="admin-tenants-provisioning-filter">
          <Select
            options={PROVISIONING_FILTER_OPTIONS}
            placeholder="Provisioning"
            value={provisioningFilter}
            onChange={(v) => {
              setProvisioningFilter(v);
              setPage(1);
            }}
          />
        </div>
        <div className="w-44" data-testid="admin-tenants-region-filter">
          <Select
            options={regionOptions}
            placeholder="Region"
            value={regionFilter}
            onChange={(v) => {
              setRegionFilter(v);
              setPage(1);
            }}
          />
        </div>
        <div className="w-44" data-testid="admin-tenants-residency-filter">
          <Select
            options={residencyOptions}
            placeholder="Residency"
            value={residencyFilter}
            onChange={(v) => {
              setResidencyFilter(v);
              setPage(1);
            }}
          />
        </div>
        <div className="w-44" data-testid="admin-tenants-trial-filter">
          <Select
            options={TRIAL_FILTER_OPTIONS}
            placeholder="Trial"
            value={trialFilter}
            onChange={(v) => {
              setTrialFilter(v as TrialFilter);
              setPage(1);
            }}
          />
        </div>
        <div className="w-44" data-testid="admin-tenants-sort">
          <Select
            options={SORT_OPTIONS}
            placeholder="Sort"
            value={sortKey}
            onChange={(v) => {
              setSortKey(v as TenantSortKey);
              setPage(1);
            }}
          />
        </div>
        {(search ||
          planFilter ||
          planIdFilter ||
          statusFilter ||
          provisioningFilter ||
          regionFilter ||
          residencyFilter ||
          trialFilter ||
          sortKey !== "created_desc") && (
          <Button
            variant="outline"
            size="sm"
            data-testid="admin-tenants-clear-filters"
            onClick={() => {
              setSearch("");
              setPlanFilter("");
              setPlanIdFilter("");
              setStatusFilter("");
              setProvisioningFilter("");
              setRegionFilter("");
              setResidencyFilter("");
              setTrialFilter("");
              setSortKey("created_desc");
              setPage(1);
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onOpenChange={setShowCreate}>
        <ModalTrigger />
        <ModalContent data-testid="admin-tenants-create-modal">
          <ModalHeader>Create New Tenant</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Name *
                </label>
                <Input
                  value={createForm.name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name: e.target.value })
                  }
                  placeholder="Acme Corp"
                  data-testid="admin-tenants-create-name"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Slug *
                </label>
                <Input
                  value={createForm.slug}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, slug: e.target.value })
                  }
                  placeholder="acme-corp"
                  data-testid="admin-tenants-create-slug"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Domain
                </label>
                <Input
                  value={createForm.domain}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, domain: e.target.value })
                  }
                  placeholder="acme.example.com"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Admin Email
                </label>
                <Input
                  type="email"
                  value={createForm.admin_email}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      admin_email: e.target.value,
                    })
                  }
                  placeholder="admin@acme.com"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Plan ID
                </label>
                <Input
                  value={createForm.plan_id}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, plan_id: e.target.value })
                  }
                  placeholder="opaque catalog id"
                  className="font-mono text-xs"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Region
                </label>
                <Input
                  value={createForm.region}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, region: e.target.value })
                  }
                  placeholder="me-central-1"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Data residency
                </label>
                <Input
                  value={createForm.data_residency}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      data_residency: e.target.value,
                    })
                  }
                  placeholder="policy tag"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Trial ends
                </label>
                <Input
                  type="date"
                  value={createForm.trial_ends_at}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      trial_ends_at: e.target.value,
                    })
                  }
                />
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Owner Platform fields synced to Backend A2. Create uses
                provision_workflow (admin_email optional for first admin).
              </p>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={
                !createForm.name || !createForm.slug || createMutation.isPending
              }
              leftIcon={
                createMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : undefined
              }
              data-testid="admin-tenants-create-submit"
            >
              {createMutation.isPending ? "Creating..." : "Create Tenant"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Tenant Table */}
      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        {isLoading ? (
          <div className="py-20 text-center text-[var(--text-muted)]">
            <Spinner className="mx-auto h-6 w-6" />
            <p className="mt-2">Loading tenants...</p>
          </div>
        ) : paginatedTenants.length === 0 ? (
          <div
            className="py-20 text-center text-[var(--text-muted)]"
            data-testid="admin-tenants-empty"
          >
            <Building2 className="mx-auto mb-2 h-10 w-10 opacity-40" />
            <p>
              {(tenants?.length ?? 0) > 0
                ? "No tenants match the current filters"
                : "No tenants found"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Name
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Domain
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Plan
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Plan ID
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Users
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Region
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Residency
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Status
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Provisioning
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Trial ends
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Created
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)] text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedTenants.map((tenant: AdminTenantListItem) => (
                  <tr
                    key={tenant.id}
                    className="border-b hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50 transition-colors"
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
                          <Building2 className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="font-medium text-[var(--text-primary)]">
                            {tenant.name}
                          </p>
                          <p className="text-xs text-[var(--text-muted)] font-mono">
                            {tenant.slug}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-[var(--text-secondary)]">
                      {tenant.domain || "-"}
                    </td>
                    <td className="p-3">
                      <Badge variant={PLAN_VARIANT[tenant.plan] || "default"}>
                        {tenant.plan}
                      </Badge>
                    </td>
                    <td
                      className="p-3 text-xs font-mono text-[var(--text-muted)]"
                      data-testid="admin-tenants-row-plan-id"
                      title="Opaque catalog plan_id (not License UUID)"
                    >
                      {tenant.plan_id || "—"}
                    </td>
                    <td className="p-3 text-sm text-[var(--text-secondary)]">
                      {tenant.user_count}
                    </td>
                    <td
                      className="p-3 text-sm text-[var(--text-secondary)]"
                      data-testid="admin-tenants-row-region"
                    >
                      {tenant.region || "—"}
                    </td>
                    <td
                      className="p-3 text-sm text-[var(--text-secondary)]"
                      data-testid="admin-tenants-row-residency"
                    >
                      {tenant.data_residency || "—"}
                    </td>
                    <td className="p-3">
                      {tenant.is_active ? (
                        <span className="inline-flex items-center gap-1 text-sm text-success-600">
                          <CheckCircle className="h-3.5 w-3.5" />{" "}
                          {activityStatusLabel(tenant)}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-sm text-danger-600">
                          <XCircle className="h-3.5 w-3.5" />{" "}
                          {activityStatusLabel(tenant)}
                        </span>
                      )}
                    </td>
                    <td className="p-3">
                      <Badge
                        variant={provisioningStatusVariant(
                          tenant.provisioning_status,
                        )}
                      >
                        {provisioningStatusLabel(tenant.provisioning_status)}
                      </Badge>
                    </td>
                    <td
                      className="p-3 text-xs text-[var(--text-muted)]"
                      data-testid="admin-tenants-row-trial"
                    >
                      {formatTrialEndsLabel(tenant.trial_ends_at)}
                    </td>
                    <td className="p-3 text-xs text-[var(--text-muted)]">
                      {new Date(tenant.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowDetail(tenant.id)}
                          data-testid="admin-tenants-detail-open"
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowDeleteConfirm(tenant.id)}
                          className="text-danger-600 hover:text-danger-700"
                          data-testid="admin-tenants-delete-open"
                        >
                          <Trash2 className="h-4 w-4" />
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

      {/* Pagination */}
      {filteredTenants.length > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--text-muted)]">
            Showing {(page - 1) * 20 + 1}-
            {Math.min(page * 20, filteredTenants.length)} of{" "}
            {filteredTenants.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              leftIcon={<ChevronRight className="h-4 w-4" />}
            />
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(1, Math.min(page - 2, totalPages - 4));
              const p = start + i;
              if (p > totalPages) return null;
              return (
                <Button
                  key={p}
                  variant={p === page ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setPage(p)}
                >
                  {p}
                </Button>
              );
            })}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              leftIcon={<ChevronLeft className="h-4 w-4" />}
            />
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && (
        <TenantDetailModal
          tenantId={showDetail}
          onClose={() => setShowDetail(null)}
        />
      )}

      {/* Delete Confirmation — FE-S04-09 soft / FE-S04-11 hard */}
      <Modal
        open={!!showDeleteConfirm}
        onOpenChange={(open) => {
          if (!open) {
            setShowDeleteConfirm(null);
            setHardDeleteConfirm(false);
          }
        }}
      >
        <ModalContent data-testid="admin-tenants-delete-modal">
          <ModalHeader>
            {hardDeleteConfirm ? "Confirm Hard Delete" : "Confirm Soft Delete"}
          </ModalHeader>
          <ModalBody>
            <div className="space-y-3">
              <p className="text-[var(--text-secondary)]">
                {hardDeleteConfirm ? "Permanently remove" : "Soft-delete"}{" "}
                tenant{" "}
                <strong>
                  {
                    tenants?.find(
                      (t: AdminTenantListItem) => t.id === showDeleteConfirm,
                    )?.name
                  }
                </strong>
                ?
              </p>
              <p className="text-sm text-[var(--text-muted)]">
                Soft-delete sets <code>is_active=false</code> (recoverable via
                Activate). Hard-delete permanently removes the row.
              </p>
              <label className="flex items-center gap-2 text-sm text-danger-600">
                <input
                  type="checkbox"
                  checked={hardDeleteConfirm}
                  onChange={(e) => setHardDeleteConfirm(e.target.checked)}
                  data-testid="admin-tenants-hard-delete-confirm"
                />
                Hard-delete (permanent — requires API confirm)
              </label>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowDeleteConfirm(null);
                setHardDeleteConfirm(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() =>
                showDeleteConfirm && handleDelete(showDeleteConfirm)
              }
              disabled={
                deleteMutation.isPending || hardDeleteMutation.isPending
              }
              className="bg-danger-600 text-white hover:bg-danger-700"
              data-testid="admin-tenants-delete-submit"
              leftIcon={
                deleteMutation.isPending || hardDeleteMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )
              }
            >
              {deleteMutation.isPending || hardDeleteMutation.isPending
                ? "Working..."
                : hardDeleteConfirm
                  ? "Hard Delete"
                  : "Soft Delete"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}

function TenantDetailModal({
  tenantId,
  onClose,
}: {
  tenantId: string;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const { data: tenant, isLoading } = useAdminTenantDetail(tenantId);
  const { data: usage } = useAdminTenantUsage(tenantId);
  const updateMutation = useUpdateAdminTenant(tenantId);
  const suspendMutation = useSuspendAdminTenant();

  const [configJson, setConfigJson] = useState("");
  const [suspendReason, setSuspendReason] = useState(
    "Suspended via Owner Console",
  );

  const handleToggleActive = useCallback(async () => {
    if (!tenant) return;
    try {
      if (tenant.is_active) {
        // FE-S04-06 — use /suspend so provisioning_status becomes suspended
        const result = await suspendMutation.mutateAsync({
          id: tenantId,
          reason: suspendReason,
        });
        toast({
          variant: "success",
          title: "Tenant suspended",
          description: formatSuspendResultDescription(
            result.tenant_id,
            result.reason,
          ),
        });
      } else {
        // FE-S04-17 — Activate recovers both soft-delete and suspend
        await updateMutation.mutateAsync({
          is_active: true,
          provisioning_status: "active",
        });
        toast({
          variant: "success",
          title: "Tenant activated",
          description:
            "is_active=true · provisioning=active (lifecycle restore)",
        });
      }
    } catch {
      toast({ variant: "error", title: "Failed to update status" });
    }
  }, [tenant, tenantId, suspendReason, suspendMutation, updateMutation, toast]);

  const handleCopy = useCallback(
    async (label: string, value: string) => {
      try {
        await navigator.clipboard.writeText(value);
        toast({
          variant: "success",
          title: `${label} copied`,
          description: value,
        });
      } catch {
        toast({ variant: "error", title: `Failed to copy ${label}` });
      }
    },
    [toast],
  );

  const handleSaveConfig = useCallback(async () => {
    try {
      const parsed = JSON.parse(configJson);
      await updateMutation.mutateAsync({ settings: parsed });
      toast({ variant: "success", title: "Configuration saved" });
    } catch {
      toast({
        variant: "error",
        title: "Invalid JSON",
        description: "Please check the configuration format.",
      });
    }
  }, [configJson, updateMutation, toast]);

  const handleSaveOwnerPlatform = useCallback(
    async (payload: TenantOwnerPlatformWritePayload) => {
      try {
        await updateMutation.mutateAsync({ ...payload });
        toast({
          variant: "success",
          title: "Owner Platform saved",
          description: "STORY-04-01 fields updated.",
        });
      } catch {
        toast({
          variant: "error",
          title: "Failed to save Owner Platform fields",
        });
      }
    },
    [updateMutation, toast],
  );

  if (isLoading) {
    return (
      <Modal open onOpenChange={(open) => !open && onClose()}>
        <ModalContent>
          <div className="py-12 text-center">
            <Spinner className="mx-auto h-6 w-6" />
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              Loading tenant details...
            </p>
          </div>
        </ModalContent>
      </Modal>
    );
  }

  return (
    <Modal open onOpenChange={(open) => !open && onClose()}>
      <ModalContent className="max-w-2xl">
        <ModalHeader>{tenant?.name || "Tenant Details"}</ModalHeader>
        <ModalBody>
          <div className="space-y-6">
            {/* FE-S04-18 — copy id/slug for ops */}
            {tenant && (
              <div
                className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-muted)]"
                data-testid="admin-tenants-copy-ids"
              >
                <span className="font-mono">id={tenant.id}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid="admin-tenants-copy-id"
                  onClick={() => handleCopy("Tenant id", tenant.id)}
                >
                  Copy id
                </Button>
                <span className="font-mono">slug={tenant.slug}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid="admin-tenants-copy-slug"
                  onClick={() => handleCopy("Tenant slug", tenant.slug)}
                >
                  Copy slug
                </Button>
              </div>
            )}
            {/* FE-S04-17 lifecycle honesty + FE-S04-06 suspend via POST /suspend */}
            <div
              className="space-y-3 rounded-lg border border-[var(--border-default)] p-4"
              data-testid="admin-tenants-status"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-[var(--text-primary)]">
                    Tenant lifecycle
                  </p>
                  <p
                    className="text-sm text-[var(--text-muted)]"
                    data-testid="admin-tenants-lifecycle-copy"
                  >
                    {tenant ? lifecycleStatusDescription(tenant) : "Loading…"}
                  </p>
                </div>
                <Button
                  variant={tenant?.is_active ? "outline" : "primary"}
                  onClick={handleToggleActive}
                  disabled={
                    updateMutation.isPending || suspendMutation.isPending
                  }
                  data-testid="admin-tenants-suspend-toggle"
                >
                  {tenant?.is_active
                    ? "Suspend"
                    : tenant && activityStatusLabel(tenant) === "Suspended"
                      ? "Activate (unsuspend)"
                      : "Activate (recover soft-delete)"}
                </Button>
              </div>
              {tenant?.is_active && (
                <div>
                  <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                    Suspend reason
                  </label>
                  <Input
                    value={suspendReason}
                    onChange={(e) => setSuspendReason(e.target.value)}
                    placeholder="Reason for suspend"
                    data-testid="admin-tenants-suspend-reason"
                  />
                </div>
              )}
            </div>

            {/* STORY-04-01 B2 read + B5 write-path — Owner Platform fields */}
            {tenant && (
              <TenantOwnerPlatformFields
                tenant={tenant}
                editable
                saving={updateMutation.isPending}
                onSave={handleSaveOwnerPlatform}
              />
            )}

            {/* Usage Stats */}
            {usage && (
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg border border-[var(--border-default)] p-3 text-center">
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {usage.api_calls.toLocaleString()}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">API Calls</p>
                </div>
                <div className="rounded-lg border border-[var(--border-default)] p-3 text-center">
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {usage.storage_mb}MB
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">Storage</p>
                </div>
                <div className="rounded-lg border border-[var(--border-default)] p-3 text-center">
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {usage.active_users}/{usage.total_users}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">
                    Active Users
                  </p>
                </div>
              </div>
            )}

            {/* Config Editor */}
            <div>
              <label className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
                Configuration (JSON)
              </label>
              <textarea
                className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--muhide-orange)] focus:ring-1 focus:ring-[var(--muhide-orange)]"
                rows={8}
                defaultValue={JSON.stringify(tenant?.settings || {}, null, 2)}
                onChange={(e) => setConfigJson(e.target.value)}
                placeholder='{"theme":"light"}'
              />
              <div className="mt-2 flex gap-2">
                <Button
                  size="sm"
                  onClick={handleSaveConfig}
                  disabled={updateMutation.isPending}
                >
                  Save Configuration
                </Button>
              </div>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
