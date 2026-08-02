"use client";

import type { ReactNode } from "react";
import { Badge } from "@salesos/ui";

/**
 * STORY-04-01 / Stream B2 — read-path display for Owner Platform tenant fields.
 * Contract: docs/program/PHASE1_STORY_04_01_PRETASK.md (A1).
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

const PROVISIONING_VARIANT: Record<
  string,
  "success" | "warning" | "default" | "danger"
> = {
  active: "success",
  pending: "warning",
  suspended: "default",
  failed: "danger",
};

function formatIsoDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function FieldRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--border-default)] py-2 last:border-b-0">
      <span className="text-sm text-[var(--text-muted)]">{label}</span>
      <span className="text-sm font-medium text-[var(--text-primary)] text-right">
        {value}
      </span>
    </div>
  );
}

export function TenantOwnerPlatformFields({
  tenant,
}: {
  tenant: TenantOwnerPlatformFieldSource;
}) {
  const status = tenant.provisioning_status ?? "pending";
  const variant = PROVISIONING_VARIANT[status] ?? "default";

  return (
    <div
      className="rounded-lg border border-[var(--border-default)] p-4"
      data-testid="tenant-owner-platform-fields"
    >
      <p className="mb-3 text-sm font-medium text-[var(--text-primary)]">
        Owner Platform
      </p>
      <p className="mb-3 text-xs text-[var(--text-muted)]">
        STORY-04-01 fields (read path). Values appear from Admin API after A2
        migrate; absent fields show placeholders until the env is upgraded.
      </p>
      <div className="space-y-0">
        <FieldRow
          label="Plan ID"
          value={
            <span className="font-mono text-xs">{tenant.plan_id || "—"}</span>
          }
        />
        <FieldRow label="Region" value={tenant.region || "—"} />
        <FieldRow
          label="Data residency"
          value={tenant.data_residency || "—"}
        />
        <FieldRow
          label="Provisioning"
          value={<Badge variant={variant}>{status}</Badge>}
        />
        <FieldRow
          label="Trial ends"
          value={formatIsoDate(tenant.trial_ends_at)}
        />
        {tenant.subscription_ends_at !== undefined && (
          <FieldRow
            label="Subscription ends"
            value={formatIsoDate(tenant.subscription_ends_at)}
          />
        )}
      </div>
    </div>
  );
}

export function provisioningStatusLabel(
  status: string | null | undefined,
): string {
  return status || "pending";
}

export function provisioningStatusVariant(
  status: string | null | undefined,
): "success" | "warning" | "default" | "danger" {
  const key = status || "pending";
  return PROVISIONING_VARIANT[key] ?? "default";
}
