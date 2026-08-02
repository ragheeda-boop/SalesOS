"use client";

import { useState, useCallback } from "react";
import {
  Input,
  Button,
  Badge,
  Card,
  Spinner,
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useToast,
} from "@salesos/ui";
import {
  Plus,
  Flag,
  ToggleLeft,
  ToggleRight,
  Loader2,
  Edit3,
} from "lucide-react";
import {
  useAdminFeatureFlags,
  useCreateAdminFeatureFlag,
  useUpdateAdminFeatureFlag,
  useAdminFlagTenants,
  useToggleAdminFlagForTenant,
} from "@/lib/hooks/adminQueries";
import type { AdminFeatureFlag } from "@/lib/api";
import { OwnerOpsPageHonesty } from "@/features/admin/OwnerOpsPageHonesty";

export default function AdminFlagsPage() {
  const { toast } = useToast();
  const [selectedFlag, setSelectedFlag] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<AdminFeatureFlag | null>(null);

  const [createForm, setCreateForm] = useState({
    key: "",
    name: "",
    description: "",
    enabled: false,
  });
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    enabled: false,
    rollout_percent: 100,
  });

  const { data: flags, isLoading } = useAdminFeatureFlags();
  const createMutation = useCreateAdminFeatureFlag();
  const updateMutation = useUpdateAdminFeatureFlag();

  const handleCreate = useCallback(async () => {
    if (!createForm.key || !createForm.name) return;
    try {
      await createMutation.mutateAsync({
        key: createForm.key,
        name: createForm.name,
        description: createForm.description || undefined,
        enabled: createForm.enabled,
      });
      setShowCreate(false);
      setCreateForm({ key: "", name: "", description: "", enabled: false });
      toast({ variant: "success", title: "Feature flag created" });
    } catch {
      toast({ variant: "error", title: "Failed to create flag" });
    }
  }, [createForm, createMutation, toast]);

  const handleEdit = useCallback(async () => {
    if (!showEdit) return;
    try {
      await updateMutation.mutateAsync({
        id: showEdit.id,
        name: editForm.name,
        description: editForm.description,
        enabled: editForm.enabled,
        rollout_percent: editForm.rollout_percent,
      });
      setShowEdit(null);
      toast({ variant: "success", title: "Flag updated" });
    } catch {
      toast({ variant: "error", title: "Failed to update flag" });
    }
  }, [showEdit, editForm, updateMutation, toast]);

  return (
    <div className="space-y-6" data-testid="admin-flags-page">
      <OwnerOpsPageHonesty surface="flags" />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            Feature Flags
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Manage feature toggles, rollout percentages, and per-tenant
            overrides.
          </p>
        </div>
        <Button
          onClick={() => setShowCreate(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          New Flag
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Flag List */}
        <div className="lg:col-span-2">
          {isLoading ? (
            <Card className="p-12 text-center">
              <Spinner className="mx-auto h-6 w-6" />
              <p className="mt-2 text-sm text-[var(--text-muted)]">
                Loading flags...
              </p>
            </Card>
          ) : !flags?.length ? (
            <Card className="p-12 text-center">
              <Flag className="mx-auto mb-3 h-10 w-10 text-[var(--text-disabled)]" />
              <p className="text-[var(--text-muted)]">
                No feature flags configured
              </p>
              <p className="mt-1 text-sm text-[var(--text-disabled)]">
                Create your first flag to start managing feature rollouts.
              </p>
            </Card>
          ) : (
            <Card className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {flags.map((flag: AdminFeatureFlag) => (
                <button
                  key={flag.id}
                  onClick={() =>
                    setSelectedFlag(selectedFlag === flag.id ? null : flag.id)
                  }
                  className={`w-full flex items-center justify-between p-4 text-left transition ${
                    selectedFlag === flag.id
                      ? "bg-[var(--muhide-orange)]/5"
                      : "hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-lg ${flag.enabled ? "bg-success-100 text-success-600 dark:bg-success-900/30" : "bg-[var(--bg-tertiary)] text-[var(--text-disabled)]"}`}
                    >
                      <Flag className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium text-[var(--text-primary)]">
                        {flag.name}
                      </p>
                      <p className="text-xs text-[var(--text-muted)] font-mono">
                        {flag.key}
                      </p>
                      {flag.description && (
                        <p className="text-xs text-[var(--text-disabled)] mt-0.5 max-w-md truncate">
                          {flag.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={flag.enabled ? "success" : "default"}>
                      {flag.enabled ? "Enabled" : "Disabled"}
                    </Badge>
                    {flag.is_global && <Badge variant="default">Global</Badge>}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditForm({
                          name: flag.name,
                          description: flag.description || "",
                          enabled: flag.enabled,
                          rollout_percent: 100,
                        });
                        setShowEdit(flag);
                      }}
                    >
                      <Edit3 className="h-4 w-4" />
                    </Button>
                  </div>
                </button>
              ))}
            </Card>
          )}
        </div>

        {/* Tenant Override Panel */}
        <div className="lg:col-span-1">
          {selectedFlag ? (
            <FlagTenantOverride flagId={selectedFlag} />
          ) : (
            <Card className="p-8 text-center">
              <ToggleLeft className="mx-auto mb-3 h-8 w-8 text-[var(--text-disabled)]" />
              <p className="text-sm text-[var(--text-muted)]">
                Select a flag to manage per-tenant overrides
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onOpenChange={setShowCreate}>
        <ModalTrigger />
        <ModalContent>
          <ModalHeader>Create Feature Flag</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Key *
                </label>
                <Input
                  value={createForm.key}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, key: e.target.value })
                  }
                  placeholder="new_dashboard"
                  className="font-mono"
                />
                <p className="mt-1 text-xs text-[var(--text-disabled)]">
                  Unique identifier for this flag (snake_case)
                </p>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Name *
                </label>
                <Input
                  value={createForm.name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name: e.target.value })
                  }
                  placeholder="New Dashboard"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Description
                </label>
                <Input
                  value={createForm.description}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      description: e.target.value,
                    })
                  }
                  placeholder="Enables the new dashboard UI"
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() =>
                    setCreateForm({
                      ...createForm,
                      enabled: !createForm.enabled,
                    })
                  }
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    createForm.enabled
                      ? "bg-[var(--muhide-orange)]"
                      : "bg-[var(--bg-tertiary)]"
                  }`}
                  role="switch"
                  aria-checked={createForm.enabled}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-[var(--bg-primary)] shadow transition-transform ${
                      createForm.enabled ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
                <span className="text-sm text-[var(--text-secondary)]">
                  Enabled by default
                </span>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={
                !createForm.key || !createForm.name || createMutation.isPending
              }
              leftIcon={
                createMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : undefined
              }
            >
              {createMutation.isPending ? "Creating..." : "Create Flag"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Modal */}
      <Modal
        open={!!showEdit}
        onOpenChange={(open) => !open && setShowEdit(null)}
      >
        <ModalContent>
          <ModalHeader>Edit Feature Flag</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Name
                </label>
                <Input
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Description
                </label>
                <Input
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  Rollout %
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={editForm.rollout_percent}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        rollout_percent: Number(e.target.value),
                      })
                    }
                    className="flex-1 accent-[var(--muhide-orange)]"
                  />
                  <span className="w-12 text-right text-sm font-mono font-medium text-[var(--text-primary)]">
                    {editForm.rollout_percent}%
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() =>
                    setEditForm({ ...editForm, enabled: !editForm.enabled })
                  }
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    editForm.enabled
                      ? "bg-[var(--muhide-orange)]"
                      : "bg-[var(--bg-tertiary)]"
                  }`}
                  role="switch"
                  aria-checked={editForm.enabled}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-[var(--bg-primary)] shadow transition-transform ${
                      editForm.enabled ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
                <span className="text-sm text-[var(--text-secondary)]">
                  {editForm.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowEdit(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleEdit}
              leftIcon={<ToggleRight className="h-4 w-4" />}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}

function FlagTenantOverride({ flagId }: { flagId: string }) {
  const { toast } = useToast();
  const { data: overrides, isLoading } = useAdminFlagTenants(flagId);
  const toggleMutation = useToggleAdminFlagForTenant(flagId);

  const handleToggle = useCallback(
    async (tenantId: string, currentEnabled: boolean) => {
      try {
        await toggleMutation.mutateAsync({
          tenantId,
          enabled: !currentEnabled,
        });
        toast({
          variant: "success",
          title: currentEnabled ? "Disabled for tenant" : "Enabled for tenant",
        });
      } catch {
        toast({ variant: "error", title: "Failed to toggle" });
      }
    },
    [toggleMutation, toast],
  );

  return (
    <Card className="p-4 space-y-4">
      <h3 className="font-semibold text-[var(--text-primary)]">
        Per-Tenant Overrides
      </h3>
      {isLoading ? (
        <div className="py-8 text-center">
          <Spinner className="mx-auto h-5 w-5" />
        </div>
      ) : !overrides?.length ? (
        <p className="py-4 text-center text-sm text-[var(--text-muted)]">
          No tenant overrides configured
        </p>
      ) : (
        <div className="space-y-2">
          {overrides.map((o) => (
            <div
              key={o.tenant_id}
              className="flex items-center justify-between rounded-lg border border-[var(--border-default)] p-3"
            >
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  {o.tenant_name}
                </p>
                <p className="text-xs text-[var(--text-muted)] font-mono">
                  {o.tenant_id}
                </p>
              </div>
              <button
                onClick={() => handleToggle(o.tenant_id, o.enabled)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  o.enabled
                    ? "bg-[var(--muhide-orange)]"
                    : "bg-[var(--bg-tertiary)]"
                }`}
                role="switch"
                aria-checked={o.enabled}
                aria-label={`${o.enabled ? "Disable" : "Enable"} for ${o.tenant_name}`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-[var(--bg-primary)] shadow transition-transform ${
                    o.enabled ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
