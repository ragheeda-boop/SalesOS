"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Badge, Button, Input, Select } from "@salesos/ui";

/**
 * STORY-04-01 / Stream B — Owner Platform tenant fields.
 * B2 read-path · B5 write-path (edit) · plan B3 AI honesty held separately.
 * Does not touch TenantList (parallel-agent reserved). No GA AI claims.
 */

export type TenantOwnerPlatformFieldSource = {
  plan_id?: string | null;
  region?: string | null;
  data_residency?: string | null;
  provisioning_status?: string | null;
  trial_ends_at?: string | null;
  subscription_ends_at?: string | null;
};

export type TenantOwnerPlatformWritePayload = {
  plan_id?: string | null;
  region?: string | null;
  data_residency?: string | null;
  provisioning_status?: string | null;
  trial_ends_at?: string | null;
};

export const PROVISIONING_STATUS_OPTIONS = [
  { label: "Pending", value: "pending" },
  { label: "Active", value: "active" },
  { label: "Suspended", value: "suspended" },
  { label: "Failed", value: "failed" },
];

const PROVISIONING_VARIANT: Record<string, "success" | "warning" | "default" | "danger"> = {
  active: "success",
  pending: "warning",
  suspended: "default",
  failed: "danger",
};

export function formatIsoDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Convert ISO datetime → yyyy-mm-dd for date inputs. */
export function toDateInputValue(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

/** Convert yyyy-mm-dd → ISO midnight UTC (or null if empty). */
export function fromDateInputValue(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const d = new Date(`${trimmed}T00:00:00.000Z`);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export function buildOwnerPlatformWritePayload(
  form: TenantOwnerPlatformWritePayload
): TenantOwnerPlatformWritePayload {
  return {
    plan_id: form.plan_id?.trim() ? form.plan_id.trim() : null,
    region: form.region?.trim() ? form.region.trim() : null,
    data_residency: form.data_residency?.trim() ? form.data_residency.trim() : null,
    provisioning_status: form.provisioning_status?.trim()
      ? form.provisioning_status.trim()
      : "pending",
    trial_ends_at: form.trial_ends_at ?? null,
  };
}

function FieldRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--border-default)] py-2 last:border-b-0">
      <span className="text-sm text-[var(--text-muted)]">{label}</span>
      <span className="text-sm font-medium text-[var(--text-primary)] text-right">{value}</span>
    </div>
  );
}

export function TenantOwnerPlatformFields({
  tenant,
  editable = false,
  saving = false,
  onSave,
}: {
  tenant: TenantOwnerPlatformFieldSource;
  editable?: boolean;
  saving?: boolean;
  onSave?: (payload: TenantOwnerPlatformWritePayload) => void | Promise<void>;
}) {
  const status = tenant.provisioning_status ?? "pending";
  const variant = PROVISIONING_VARIANT[status] ?? "default";

  const [planId, setPlanId] = useState(tenant.plan_id ?? "");
  const [region, setRegion] = useState(tenant.region ?? "");
  const [dataResidency, setDataResidency] = useState(tenant.data_residency ?? "");
  const [provisioningStatus, setProvisioningStatus] = useState(status);
  const [trialEnds, setTrialEnds] = useState(toDateInputValue(tenant.trial_ends_at));

  useEffect(() => {
    setPlanId(tenant.plan_id ?? "");
    setRegion(tenant.region ?? "");
    setDataResidency(tenant.data_residency ?? "");
    setProvisioningStatus(tenant.provisioning_status ?? "pending");
    setTrialEnds(toDateInputValue(tenant.trial_ends_at));
  }, [tenant]);

  const handleSave = () => {
    if (!onSave) return;
    void onSave(
      buildOwnerPlatformWritePayload({
        plan_id: planId,
        region,
        data_residency: dataResidency,
        provisioning_status: provisioningStatus,
        trial_ends_at: fromDateInputValue(trialEnds),
      })
    );
  };

  return (
    <div
      className="rounded-lg border border-[var(--border-default)] p-4"
      data-testid="tenant-owner-platform-fields"
    >
      <p className="mb-3 text-sm font-medium text-[var(--text-primary)]">Owner Platform</p>
      <p className="mb-3 text-xs text-[var(--text-muted)]">
        STORY-04-01 fields
        {editable
          ? " (write path). Full provisioning workflow remains script-first (STORY-04-02)."
          : " (read path). Placeholders until Admin API returns values."}
      </p>

      {!editable ? (
        <div className="space-y-0">
          <FieldRow
            label="Plan ID"
            value={<span className="font-mono text-xs">{tenant.plan_id || "—"}</span>}
          />
          <FieldRow label="Region" value={tenant.region || "—"} />
          <FieldRow label="Data residency" value={tenant.data_residency || "—"} />
          <FieldRow label="Provisioning" value={<Badge variant={variant}>{status}</Badge>} />
          <FieldRow label="Trial ends" value={formatIsoDate(tenant.trial_ends_at)} />
          {tenant.subscription_ends_at !== undefined && (
            <FieldRow
              label="Subscription ends"
              value={formatIsoDate(tenant.subscription_ends_at)}
            />
          )}
        </div>
      ) : (
        <div className="space-y-3" data-testid="tenant-owner-platform-edit">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Plan ID
            </label>
            <Input
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              placeholder="opaque catalog id"
              className="font-mono text-xs"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Region
            </label>
            <Input
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              placeholder="me-central-1"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Data residency
            </label>
            <Input
              value={dataResidency}
              onChange={(e) => setDataResidency(e.target.value)}
              placeholder="policy tag"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Provisioning status
            </label>
            <Select
              options={PROVISIONING_STATUS_OPTIONS}
              value={provisioningStatus}
              onChange={(v) => setProvisioningStatus(v)}
              placeholder="Status"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
              Trial ends
            </label>
            <Input type="date" value={trialEnds} onChange={(e) => setTrialEnds(e.target.value)} />
          </div>
          <div className="flex justify-end pt-1">
            <Button size="sm" onClick={handleSave} disabled={saving || !onSave}>
              {saving ? "Saving..." : "Save Owner Platform"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export function provisioningStatusLabel(status: string | null | undefined): string {
  return status || "pending";
}

export function provisioningStatusVariant(
  status: string | null | undefined
): "success" | "warning" | "default" | "danger" {
  const key = status || "pending";
  return PROVISIONING_VARIANT[key] ?? "default";
}
