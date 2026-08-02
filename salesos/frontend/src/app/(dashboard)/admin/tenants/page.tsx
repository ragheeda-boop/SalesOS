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
  useDeleteAdminTenant,
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

const PLAN_OPTIONS = [
  { label: "All Plans", value: "" },
  { label: "Free", value: "free" },
  { label: "Starter", value: "starter" },
  { label: "Growth", value: "growth" },
  { label: "Enterprise", value: "enterprise" },
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
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null,
  );

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

  const { data: tenants, isLoading } = useAdminTenants({
    search: search || undefined,
    plan: planFilter || undefined,
  });

  const createMutation = useCreateAdminTenant();
  const deleteMutation = useDeleteAdminTenant();

  const filteredTenants = useMemo(() => {
    if (!tenants) return [];
    let list = tenants;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (t: AdminTenantListItem) =>
          t.name.toLowerCase().includes(q) ||
          t.slug.toLowerCase().includes(q) ||
          (t.domain || "").toLowerCase().includes(q),
      );
    }
    if (planFilter)
      list = list.filter((t: AdminTenantListItem) => t.plan === planFilter);
    return list;
  }, [tenants, search, planFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredTenants.length / 20));
  const paginatedTenants = filteredTenants.slice((page - 1) * 20, page * 20);

  const handleCreate = useCallback(async () => {
    if (!createForm.name || !createForm.slug) return;
    try {
      await createMutation.mutateAsync({
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
        title: "Tenant created",
        description:
          "Provisioned via Admin API (STORY-04-02 workflow). Confirm Studio seed in target env.",
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
        await deleteMutation.mutateAsync(id);
        setShowDeleteConfirm(null);
        toast({
          variant: "success",
          title: "Tenant deleted",
          description: "The tenant has been permanently removed.",
        });
      } catch {
        toast({
          variant: "error",
          title: "Failed to delete",
          description: "An error occurred while deleting the tenant.",
        });
      }
    },
    [deleteMutation, toast],
  );

  return (
    <div className="space-y-6">
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
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onOpenChange={setShowCreate}>
        <ModalTrigger />
        <ModalContent>
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
          <div className="py-20 text-center text-[var(--text-muted)]">
            <Building2 className="mx-auto mb-2 h-10 w-10 opacity-40" />
            <p>No tenants found</p>
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
                    Users
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Status
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Provisioning
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
                    <td className="p-3 text-sm text-[var(--text-secondary)]">
                      {tenant.user_count}
                    </td>
                    <td className="p-3">
                      {tenant.is_active ? (
                        <span className="inline-flex items-center gap-1 text-sm text-success-600">
                          <CheckCircle className="h-3.5 w-3.5" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-sm text-danger-600">
                          <XCircle className="h-3.5 w-3.5" /> Suspended
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
                    <td className="p-3 text-xs text-[var(--text-muted)]">
                      {new Date(tenant.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowDetail(tenant.id)}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowDeleteConfirm(tenant.id)}
                          className="text-danger-600 hover:text-danger-700"
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

      {/* Delete Confirmation */}
      <Modal
        open={!!showDeleteConfirm}
        onOpenChange={(open) => !open && setShowDeleteConfirm(null)}
      >
        <ModalContent>
          <ModalHeader>Confirm Deletion</ModalHeader>
          <ModalBody>
            <div className="space-y-3">
              <p className="text-[var(--text-secondary)]">
                Are you sure you want to delete tenant{" "}
                <strong>
                  {
                    tenants?.find(
                      (t: AdminTenantListItem) => t.id === showDeleteConfirm,
                    )?.name
                  }
                </strong>
                ?
              </p>
              <p className="text-sm text-danger-600">
                This action cannot be undone. All data will be permanently
                removed.
              </p>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteConfirm(null)}
            >
              Cancel
            </Button>
            <Button
              onClick={() =>
                showDeleteConfirm && handleDelete(showDeleteConfirm)
              }
              disabled={deleteMutation.isPending}
              className="bg-danger-600 text-white hover:bg-danger-700"
              leftIcon={
                deleteMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )
              }
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete Tenant"}
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

  const [configJson, setConfigJson] = useState("");

  const handleToggleActive = useCallback(async () => {
    if (!tenant) return;
    try {
      await updateMutation.mutateAsync({ is_active: !tenant.is_active });
      toast({
        variant: "success",
        title: tenant.is_active ? "Tenant suspended" : "Tenant activated",
      });
    } catch {
      toast({ variant: "error", title: "Failed to update status" });
    }
  }, [tenant, updateMutation, toast]);

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
            {/* Status Toggle */}
            <div className="flex items-center justify-between rounded-lg border border-[var(--border-default)] p-4">
              <div>
                <p className="font-medium text-[var(--text-primary)]">
                  Tenant Status
                </p>
                <p className="text-sm text-[var(--text-muted)]">
                  {tenant?.is_active ? "Active" : "Suspended"}
                </p>
              </div>
              <Button
                variant={tenant?.is_active ? "outline" : "primary"}
                onClick={handleToggleActive}
                disabled={updateMutation.isPending}
              >
                {tenant?.is_active ? "Suspend" : "Activate"}
              </Button>
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
