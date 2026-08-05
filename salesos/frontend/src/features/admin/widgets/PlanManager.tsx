"use client";

import { useState } from "react";
import { Button, Badge, Card, Spinner, useToast } from "@salesos/ui";
import { Plus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import {
  useAdminPlans,
  useAdminLicenses,
  useCreateAdminPlan,
  useCreateAdminLicense,
  useUpdateAdminPlan,
} from "@/lib/hooks/adminQueries";
import { AdminPlan, AdminLicense } from "@/lib/api";
import {
  formatPlanEntitlementsSummary,
  parsePlanEntitlementsJson,
} from "@/features/admin/lib/formatProvisionToast";

/**
 * Owner plans UI — STORY-06-01 entitlements display/editor (tip 2f0e96c).
 * Leave entitlements JSON empty on create → BE tier defaults. Not Production GO.
 */
export function PlanManager() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const { data: plans, isLoading: plansLoading } = useAdminPlans();
  const { data: licenses, isLoading: licensesLoading } = useAdminLicenses();
  const [showCreatePlan, setShowCreatePlan] = useState(false);
  const [showCreateLicense, setShowCreateLicense] = useState(false);
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [entitlementsJson, setEntitlementsJson] = useState("");
  const [editEntitlementsJson, setEditEntitlementsJson] = useState("");
  const [planForm, setPlanForm] = useState({
    name: "",
    tier: "free" as "free" | "starter" | "growth" | "enterprise",
    price_monthly: 0,
    max_users: 1,
    max_storage_mb: 100,
    max_api_calls: 1000,
    features: "",
  });
  const [licenseForm, setLicenseForm] = useState({
    tenant_id: "",
    plan_id: "",
  });

  const createPlanMutation = useCreateAdminPlan();
  const createLicenseMutation = useCreateAdminLicense();
  const updatePlanMutation = useUpdateAdminPlan(editingPlanId || "");

  const handleCreatePlan = async () => {
    const parsed = parsePlanEntitlementsJson(entitlementsJson);
    if (!parsed.ok) {
      toast({
        variant: "error",
        title: "Invalid entitlements JSON",
        description: parsed.error,
      });
      return;
    }
    try {
      await createPlanMutation.mutateAsync({
        ...planForm,
        features: planForm.features
          .split(",")
          .map((f: string) => f.trim())
          .filter(Boolean),
        ...(parsed.value ? { entitlements: parsed.value } : {}),
      });
      setShowCreatePlan(false);
      setEntitlementsJson("");
      setPlanForm({
        name: "",
        tier: "free",
        price_monthly: 0,
        max_users: 1,
        max_storage_mb: 100,
        max_api_calls: 1000,
        features: "",
      });
      toast({
        variant: "success",
        title: "Plan created",
        description: parsed.value
          ? "Custom entitlements saved."
          : "BE applied tier default entitlements.",
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Create plan failed",
        description: err instanceof Error ? err.message : "create plan failed",
      });
    }
  };

  const openEditEntitlements = (plan: AdminPlan) => {
    setEditingPlanId(plan.id);
    setEditEntitlementsJson(plan.entitlements ? JSON.stringify(plan.entitlements, null, 2) : "");
  };

  const handleSaveEntitlements = async () => {
    if (!editingPlanId) return;
    const parsed = parsePlanEntitlementsJson(editEntitlementsJson);
    if (!parsed.ok) {
      toast({
        variant: "error",
        title: "Invalid entitlements JSON",
        description: parsed.error,
      });
      return;
    }
    if (!parsed.value) {
      toast({
        variant: "error",
        title: "Entitlements required",
        description: "Paste a JSON object or cancel. Empty clears not supported.",
      });
      return;
    }
    try {
      await updatePlanMutation.mutateAsync({ entitlements: parsed.value });
      setEditingPlanId(null);
      setEditEntitlementsJson("");
      toast({
        variant: "success",
        title: "Entitlements saved",
        description: formatPlanEntitlementsSummary(
          parsed.value as Parameters<typeof formatPlanEntitlementsSummary>[0]
        ),
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Update entitlements failed",
        description: err instanceof Error ? err.message : "update plan failed",
      });
    }
  };

  if (plansLoading || licensesLoading) {
    return (
      <div className="py-20 text-center text-[var(--text-muted)]">
        <Spinner /> {t("admin.plan_manager.loading")}
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-plan-manager">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t("admin.plan_manager.title")}</h2>
        <div className="flex gap-2">
          <Button onClick={() => setShowCreateLicense(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            {t("admin.plan_manager.new_license")}
          </Button>
          <Button
            onClick={() => setShowCreatePlan(true)}
            className="gap-2"
            data-testid="admin-plans-new"
          >
            <Plus className="h-4 w-4" />
            {t("admin.plan_manager.new_plan")}
          </Button>
        </div>
      </div>

      {showCreatePlan && (
        <Card className="p-4 space-y-3" data-testid="admin-plans-create">
          <h3 className="font-semibold">{t("admin.plan_manager.new_plan_title")}</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder={t("admin.plan_manager.name_placeholder")}
              value={planForm.name}
              onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
            />
            <select
              className="border rounded px-3 py-2 text-sm"
              value={planForm.tier}
              onChange={(e) =>
                setPlanForm({
                  ...planForm,
                  tier: e.target.value as "free" | "starter" | "growth" | "enterprise",
                })
              }
            >
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="growth">Growth</option>
              <option value="enterprise">Enterprise</option>
            </select>
            <input
              className="border rounded px-3 py-2 text-sm"
              type="number"
              placeholder={t("admin.plan_manager.price_placeholder")}
              value={planForm.price_monthly}
              onChange={(e) =>
                setPlanForm({
                  ...planForm,
                  price_monthly: Number(e.target.value),
                })
              }
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              type="number"
              placeholder={t("admin.plan_manager.max_users_placeholder")}
              value={planForm.max_users}
              onChange={(e) => setPlanForm({ ...planForm, max_users: Number(e.target.value) })}
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              type="number"
              placeholder={t("admin.plan_manager.storage_placeholder")}
              value={planForm.max_storage_mb}
              onChange={(e) =>
                setPlanForm({
                  ...planForm,
                  max_storage_mb: Number(e.target.value),
                })
              }
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              type="number"
              placeholder={t("admin.plan_manager.api_calls_placeholder")}
              value={planForm.max_api_calls}
              onChange={(e) =>
                setPlanForm({
                  ...planForm,
                  max_api_calls: Number(e.target.value),
                })
              }
            />
            <input
              className="border rounded px-3 py-2 text-sm col-span-full"
              placeholder={t("admin.plan_manager.features_placeholder")}
              value={planForm.features}
              onChange={(e) => setPlanForm({ ...planForm, features: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Entitlements JSON (optional — empty uses BE tier defaults)
            </label>
            <textarea
              className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs text-[var(--text-primary)]"
              rows={6}
              placeholder='{"version":1,"domains":{...},"quotas":{...},"deployment_tier":"pooled","support_sla":"community"}'
              value={entitlementsJson}
              onChange={(e) => setEntitlementsJson(e.target.value)}
              data-testid="admin-plans-entitlements-json"
            />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleCreatePlan}
              disabled={createPlanMutation.isPending}
              data-testid="admin-plans-create-submit"
            >
              {t("admin.plan_manager.create_btn")}
            </Button>
            <Button variant="ghost" onClick={() => setShowCreatePlan(false)}>
              {t("admin.plan_manager.cancel")}
            </Button>
          </div>
        </Card>
      )}

      {showCreateLicense && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">{t("admin.plan_manager.new_license_title")}</h3>
          <div className="grid grid-cols-2 gap-3">
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder={t("admin.plan_manager.tenant_id_placeholder")}
              value={licenseForm.tenant_id}
              onChange={(e) => setLicenseForm({ ...licenseForm, tenant_id: e.target.value })}
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder={t("admin.plan_manager.plan_id_placeholder")}
              value={licenseForm.plan_id}
              onChange={(e) => setLicenseForm({ ...licenseForm, plan_id: e.target.value })}
            />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={async () => {
                await createLicenseMutation.mutateAsync({
                  tenant_id: licenseForm.tenant_id,
                  plan_id: licenseForm.plan_id,
                });
                setShowCreateLicense(false);
              }}
              disabled={createLicenseMutation.isPending}
            >
              {t("admin.plan_manager.create_btn")}
            </Button>
            <Button variant="ghost" onClick={() => setShowCreateLicense(false)}>
              {t("admin.plan_manager.cancel")}
            </Button>
          </div>
        </Card>
      )}

      {editingPlanId && (
        <Card className="p-4 space-y-3" data-testid="admin-plans-entitlements-edit">
          <h3 className="font-semibold">Edit entitlements — plan {editingPlanId}</h3>
          <p className="text-xs text-[var(--text-muted)]">
            STORY-06-01 JSONB document. Domains keys must be DOM-* . Not Production GO.
          </p>
          <textarea
            className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs text-[var(--text-primary)]"
            rows={12}
            value={editEntitlementsJson}
            onChange={(e) => setEditEntitlementsJson(e.target.value)}
            data-testid="admin-plans-entitlements-edit-json"
          />
          <div className="flex gap-2">
            <Button
              onClick={handleSaveEntitlements}
              disabled={updatePlanMutation.isPending}
              data-testid="admin-plans-entitlements-save"
            >
              {updatePlanMutation.isPending ? "Saving…" : "Save entitlements"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setEditingPlanId(null);
                setEditEntitlementsJson("");
              }}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-4">
          <h3 className="font-semibold mb-3">
            {t("admin.plan_manager.plans_section", {
              count: plans?.length || 0,
            })}
          </h3>
          <div className="space-y-3">
            {plans?.map((plan: AdminPlan) => (
              <div key={plan.id} className="border rounded-lg p-3" data-testid="admin-plans-row">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{plan.name}</span>
                  <Badge
                    variant={
                      plan.tier === "enterprise"
                        ? "success"
                        : plan.tier === "free"
                          ? "default"
                          : "warning"
                    }
                  >
                    {plan.tier}
                  </Badge>
                </div>
                <div className="text-sm text-[var(--text-muted)] space-y-1">
                  <p>
                    SAR {plan.price_monthly}/شهرياً | SAR {plan.price_yearly}
                    /سنوياً
                  </p>
                  <p>
                    {plan.max_users} مستخدم | {plan.max_storage_mb} MB |{" "}
                    {plan.max_api_calls.toLocaleString()} استدعاء
                  </p>
                  <p className="font-mono text-xs" data-testid="admin-plans-entitlements-summary">
                    {formatPlanEntitlementsSummary(plan.entitlements)}
                  </p>
                  {plan.features?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {plan.features.map((f: string) => (
                        <Badge key={f} variant="default">
                          {f}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-2"
                    onClick={() => openEditEntitlements(plan)}
                    data-testid="admin-plans-entitlements-edit-open"
                  >
                    Edit entitlements
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-semibold mb-3">
            {t("admin.plan_manager.licenses_section", {
              count: licenses?.length || 0,
            })}
          </h3>
          <div className="space-y-3">
            {licenses?.map((lic: AdminLicense) => (
              <div key={lic.id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{lic.tenant_name}</span>
                  <Badge variant={lic.is_active ? "success" : "default"}>
                    {lic.is_active
                      ? t("admin.plan_manager.active")
                      : t("admin.plan_manager.inactive")}
                  </Badge>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  {lic.plan_name} ({lic.tier})
                </p>
                {lic.ends_at && (
                  <p className="text-xs text-[var(--text-disabled)]">
                    ينتهي: {new Date(lic.ends_at).toLocaleDateString("ar-SA")}
                  </p>
                )}
              </div>
            ))}
            {(!licenses || licenses.length === 0) && (
              <p className="text-sm text-[var(--text-muted)] text-center py-4">
                {t("admin.plan_manager.no_licenses")}
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
