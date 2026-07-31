"use client";

import { useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listAdminAuditLogs,
  listAdminFeatureFlags,
  listAdminRoles,
  listAdminUsers,
  type AdminFeatureFlag,
  type AdminRole,
  type AdminUser,
  type AuditLogEntry,
} from "@/lib/api";
import { adminKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../_components/page-header";
import {
  DomainWorkbench,
  type DomainSection,
} from "../_components/domain-workbench";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
  PreviewBadge,
} from "../_components/states";
import { formatCount, formatWhen } from "../_components/format";
import { useAccessToken } from "../_hooks/useAccessToken";

function PreviewPanel({
  children,
  legacyHref,
  legacyLabel = "Open legacy admin",
}: {
  children: ReactNode;
  legacyHref?: string;
  legacyLabel?: string;
}) {
  return (
    <div className="space-y-3 text-sm text-[var(--text-secondary)]">
      <div className="flex items-center gap-2">
        <PreviewBadge />
        <span className="text-[12px] text-[var(--text-muted)]">
          Not wired — no invented controls
        </span>
      </div>
      <p>{children}</p>
      {legacyHref ? (
        <GhostButtonLink href={legacyHref}>{legacyLabel}</GhostButtonLink>
      ) : null}
    </div>
  );
}

function UsersPanel({
  ready,
  hasToken,
}: {
  ready: boolean;
  hasToken: boolean;
}) {
  const query = useQuery({
    queryKey: adminKeys.users({ page_size: "50" }),
    queryFn: () => listAdminUsers({ page_size: "50" }),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/admin" />;
  if (query.isLoading) return <LoadingState label="Loading users…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load users"
        description={
          query.error instanceof Error
            ? query.error.message
            : "Admin APIs often require elevated permissions."
        }
        onRetry={() => void query.refetch()}
      />
    );
  }

  const users: AdminUser[] = query.data ?? [];
  if (users.length === 0) {
    return (
      <EmptyState
        title="No users returned"
        description="This tenant has no admin-visible users, or the list is empty."
        action={
          <GhostButtonLink href="/admin">Open legacy admin</GhostButtonLink>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-[var(--text-muted)]" aria-live="polite">
        {formatCount(users.length)} user{users.length === 1 ? "" : "s"} ·
        read-only dual-run list
      </p>
      <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse text-left text-sm">
            <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
              <tr>
                <th scope="col" className="px-3 py-2 font-medium">
                  Name
                </th>
                <th scope="col" className="px-3 py-2 font-medium">
                  Email
                </th>
                <th scope="col" className="px-3 py-2 font-medium">
                  Role
                </th>
                <th scope="col" className="px-3 py-2 font-medium">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-[var(--border-default)] last:border-b-0"
                >
                  <td className="px-3 py-2 font-medium text-[var(--text-primary)]">
                    {user.full_name || "—"}
                    {user.full_name_ar ? (
                      <p
                        className="mt-0.5 text-[12px] font-normal text-[var(--text-muted)]"
                        dir="auto"
                      >
                        {user.full_name_ar}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">
                    {user.email}
                  </td>
                  <td className="px-3 py-2 capitalize text-[var(--text-secondary)]">
                    {user.role?.replace(/_/g, " ") || "—"}
                  </td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">
                    {user.is_active ? "Active" : "Inactive"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <GhostButtonLink href="/admin">Manage in legacy admin</GhostButtonLink>
    </div>
  );
}

function RolesPanel({
  ready,
  hasToken,
}: {
  ready: boolean;
  hasToken: boolean;
}) {
  const query = useQuery({
    queryKey: adminKeys.roles(),
    queryFn: () => listAdminRoles(),
    enabled: ready && hasToken,
    staleTime: 30_000,
  });

  if (query.isLoading) return <LoadingState label="Loading roles…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load roles"
        description={
          query.error instanceof Error ? query.error.message : "Request failed"
        }
        onRetry={() => void query.refetch()}
      />
    );
  }

  const roles: AdminRole[] = query.data ?? [];
  if (roles.length === 0) {
    return (
      <EmptyState
        title="No roles"
        description="RBAC roles API returned an empty list."
        action={
          <GhostButtonLink href="/admin">Open legacy admin</GhostButtonLink>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-[var(--text-muted)]">
        {formatCount(roles.length)} role{roles.length === 1 ? "" : "s"} ·
        permission counts only
      </p>
      <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
        {roles.map((role) => (
          <li
            key={role.id}
            className="border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-medium text-[var(--text-primary)]">
                {role.name}
              </span>
              <span className="text-[12px] text-[var(--text-muted)]">
                {formatCount(role.user_count)} users ·{" "}
                {formatCount(role.permissions?.length ?? 0)} permissions
                {role.is_system ? " · system" : ""}
              </span>
            </div>
            {role.description ? (
              <p className="mt-1 text-[12px] text-[var(--text-muted)]">
                {role.description}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
      <p className="text-[12px] text-[var(--text-muted)]">
        Full permission matrix editing stays in legacy admin — this panel is
        read-only.
      </p>
    </div>
  );
}

function FlagsPanel({
  ready,
  hasToken,
}: {
  ready: boolean;
  hasToken: boolean;
}) {
  const query = useQuery({
    queryKey: adminKeys.featureFlags(),
    queryFn: () => listAdminFeatureFlags(),
    enabled: ready && hasToken,
    staleTime: 30_000,
  });

  if (query.isLoading) return <LoadingState label="Loading feature flags…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load flags"
        description={
          query.error instanceof Error ? query.error.message : "Request failed"
        }
        onRetry={() => void query.refetch()}
      />
    );
  }

  const flags: AdminFeatureFlag[] = query.data ?? [];
  if (flags.length === 0) {
    return (
      <EmptyState
        title="No feature flags"
        description="No flags configured for this environment."
        action={
          <GhostButtonLink href="/admin/flags">
            Open legacy flags
          </GhostButtonLink>
        }
      />
    );
  }

  const aiFlags = flags.filter((f) => /ai|copilot/i.test(`${f.key} ${f.name}`));

  return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--text-secondary)]">
        Read-only list. Toggles are not exposed here — changing GA AI flags
        requires honesty review (
        <code className="mx-1 font-mono text-[12px]">AI_HONESTY.md</code>). Ask
        AI remains popup-only.
      </p>
      {aiFlags.length > 0 ? (
        <p className="text-[12px] text-[var(--text-muted)]">
          {formatCount(aiFlags.length)} flag{aiFlags.length === 1 ? "" : "s"}{" "}
          mention AI/copilot — default product policy keeps copilot off unless
          evidence-validated.
        </p>
      ) : null}
      <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
        {flags.map((flag) => (
          <li
            key={flag.id}
            className="flex flex-wrap items-start justify-between gap-2 border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
          >
            <span className="min-w-0">
              <span className="font-medium text-[var(--text-primary)]">
                {flag.name}
              </span>
              <span className="mt-0.5 block font-mono text-[12px] text-[var(--text-muted)]">
                {flag.key}
              </span>
              {flag.description ? (
                <span className="mt-1 block text-[12px] text-[var(--text-muted)]">
                  {flag.description}
                </span>
              ) : null}
            </span>
            <span
              className={
                flag.enabled
                  ? "shrink-0 text-[12px] font-medium text-[var(--text-secondary)]"
                  : "shrink-0 text-[12px] text-[var(--text-muted)]"
              }
            >
              {flag.enabled ? "On" : "Off"}
              {flag.is_global ? " · global" : ""}
            </span>
          </li>
        ))}
      </ul>
      <GhostButtonLink href="/admin/flags">
        Manage flags in legacy
      </GhostButtonLink>
    </div>
  );
}

function AuditPanel({
  ready,
  hasToken,
}: {
  ready: boolean;
  hasToken: boolean;
}) {
  const query = useQuery({
    queryKey: adminKeys.auditLogs({ page_size: 25 }),
    queryFn: () =>
      listAdminAuditLogs({
        page_size: 25,
        tenant_id: getTenantId(),
      }),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  if (query.isLoading) return <LoadingState label="Loading audit logs…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load audit logs"
        description={
          query.error instanceof Error ? query.error.message : "Request failed"
        }
        onRetry={() => void query.refetch()}
      />
    );
  }

  const rows: AuditLogEntry[] = query.data?.items ?? [];

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No audit entries"
        description="No recent audit log rows for this tenant."
        action={
          <GhostButtonLink href="/admin/audit">
            Open legacy audit
          </GhostButtonLink>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-[var(--text-muted)]">
        Showing up to 25 recent entries · read-only
      </p>
      <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
        {rows.slice(0, 25).map((entry) => (
          <li
            key={entry.id}
            className="border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-medium capitalize text-[var(--text-primary)]">
                {entry.action?.replace(/_/g, " ") ||
                  entry.action_type ||
                  "Action"}
              </span>
              <span className="text-[12px] text-[var(--text-muted)]">
                {formatWhen(entry.created_at)}
              </span>
            </div>
            <p className="mt-0.5 text-[12px] text-[var(--text-muted)]">
              {entry.actor_name ||
                entry.actor_email ||
                entry.actor_id ||
                "Unknown actor"}
              {entry.resource_type || entry.resource
                ? ` · ${entry.resource_type || entry.resource}${
                    entry.resource_id ? ` ${entry.resource_id}` : ""
                  }`
                : null}
            </p>
          </li>
        ))}
      </ul>
      <GhostButtonLink href="/admin/audit">
        Full audit in legacy
      </GhostButtonLink>
    </div>
  );
}

export default function V3AdminPage() {
  const { ready, hasToken } = useAccessToken();

  const sections: DomainSection[] = useMemo(
    () => [
      {
        id: "users",
        label: "Users",
        audience: "Admins",
        description:
          "Workspace members from the admin users API — read-only dual-run.",
        body: <UsersPanel ready={ready} hasToken={hasToken} />,
      },
      {
        id: "roles",
        label: "Roles",
        audience: "Admins",
        description:
          "Named roles and permission counts. Matrix editing stays in legacy.",
        body:
          ready && hasToken ? (
            <RolesPanel ready={ready} hasToken={hasToken} />
          ) : !ready ? (
            <LoadingState />
          ) : (
            <PermissionState nextPath="/v3/admin" />
          ),
      },
      {
        id: "rbac",
        label: "RBAC matrix",
        audience: "Security",
        description:
          "Permission matrix by role × resource — governance surface.",
        body: (
          <PreviewPanel legacyHref="/admin">
            Interactive RBAC matrix is not dual-run yet. Use Roles for a
            read-only permission count summary, or legacy admin for edits that
            must stay audited.
          </PreviewPanel>
        ),
      },
      {
        id: "orgs",
        label: "Organizations",
        audience: "Admins",
        description: "Tenant orgs, workspaces, and environment labels.",
        body: (
          <PreviewPanel legacyHref="/admin">
            Multi-tenant org browser stays on legacy admin tenants until a
            dedicated v3 org 360 ships.
          </PreviewPanel>
        ),
      },
      {
        id: "integrations",
        label: "Integrations",
        audience: "Admins",
        description: "Connected apps, sync health, and credentials rotation.",
        body: (
          <PreviewPanel legacyHref="/admin">
            Integration health is not wired on this surface. Prefer legacy admin
            for credential rotation.
          </PreviewPanel>
        ),
      },
      {
        id: "billing",
        label: "Billing",
        audience: "Billing admins",
        description:
          "Plan, seats, and invoices (when commercial module is live).",
        body: (
          <PreviewPanel legacyHref="/admin">
            Billing invoices/transactions exist as admin APIs but are not
            dual-run here yet — avoid accidental commercial actions in the spike
            shell.
          </PreviewPanel>
        ),
      },
      {
        id: "audit",
        label: "Audit logs",
        audience: "Security",
        description: "Recent immutable action history for compliance review.",
        body:
          ready && hasToken ? (
            <AuditPanel ready={ready} hasToken={hasToken} />
          ) : !ready ? (
            <LoadingState />
          ) : (
            <PermissionState nextPath="/v3/admin" />
          ),
      },
      {
        id: "flags",
        label: "Feature flags",
        audience: "Admins",
        description:
          "Module and Preview flags. AI copilot stays off by default.",
        body:
          ready && hasToken ? (
            <FlagsPanel ready={ready} hasToken={hasToken} />
          ) : !ready ? (
            <LoadingState />
          ) : (
            <PermissionState nextPath="/v3/admin" />
          ),
      },
      {
        id: "security",
        label: "Security",
        audience: "Security",
        description: "SSO, session policy, and API key governance.",
        body: (
          <PreviewPanel legacyHref="/settings">
            SSO / session policy UI is not dual-run. Do not weaken auth from
            this shell.
          </PreviewPanel>
        ),
      },
      {
        id: "api",
        label: "API keys",
        audience: "Admins",
        description: "Machine credentials and webhook endpoints.",
        body: (
          <PreviewPanel
            legacyHref="/v3/settings"
            legacyLabel="Open v3 Settings · API"
          >
            API key listing lives under Settings → API in this dual-run shell
            (same settings API).
          </PreviewPanel>
        ),
      },
    ],
    [ready, hasToken],
  );

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <PageHeader
        title="Admin"
        description="Governance domain — live users, roles, flags, and audit where APIs allow. Dangerous toggles stay in legacy."
        actions={<GhostButtonLink href="/admin">Legacy admin</GhostButtonLink>}
      />
      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/admin" />
      ) : (
        <DomainWorkbench sections={sections} defaultId="users" />
      )}
    </div>
  );
}
