"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState } from "react";
import {
  Input,
  Button,
  Badge,
  Card,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useToast,
} from "@salesos/ui";
import { Search, Shield, UserX, CheckCircle, XCircle, UserPlus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { useAdminUsers, useDeactivateAdminUser } from "@/lib/hooks/adminQueries";
import { AdminUser } from "@/lib/api";
import api from "@/lib/api";

interface InviteResult {
  message: string;
  user_id: string;
  email?: string;
  role?: string;
  email_delivery: string;
  temporary_password?: string;
}

export function UserList() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("user");
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [inviteResult, setInviteResult] = useState<InviteResult | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const {
    data: users,
    isLoading,
    refetch,
  } = useAdminUsers({
    search: search || undefined,
    role: roleFilter || undefined,
  });
  const deactivateMutation = useDeactivateAdminUser();

  const handleDeactivate = async (id: string) => {
    await deactivateMutation.mutateAsync(id);
  };

  const resetInviteForm = () => {
    setInviteEmail("");
    setInviteRole("user");
    setInviteResult(null);
    setInviteError(null);
    setInviteSubmitting(false);
  };

  const handleInviteOpenChange = (open: boolean) => {
    setInviteOpen(open);
    if (!open) resetInviteForm();
  };

  const handleInviteSubmit = async () => {
    const email = inviteEmail.trim();
    if (!email || !email.includes("@")) {
      const msg = "Enter a valid email address.";
      setInviteError(msg);
      toast({
        title: "Email required",
        description: msg,
        variant: "error",
      });
      return;
    }
    setInviteSubmitting(true);
    setInviteError(null);
    try {
      const res = await api.post<InviteResult>("/api/v1/identity/invite", {
        email,
        role: inviteRole,
      });
      setInviteResult(res.data);
      toast({
        title: "User invited",
        description:
          res.data.email_delivery === "not_configured"
            ? "Account created. Email is not configured — share credentials out of band."
            : res.data.message,
        variant: "success",
      });
      void refetch();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      const msg =
        typeof detail === "string" ? detail : err instanceof Error ? err.message : "Request failed";
      setInviteError(msg);
      toast({
        title: "Invite failed",
        description: msg,
        variant: "error",
      });
    } finally {
      setInviteSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-xl font-bold">{t("admin.user_list.title")}</h2>
        <Button size="sm" onClick={() => setInviteOpen(true)} data-testid="admin-invite-user-open">
          <UserPlus className="h-4 w-4 ml-1" />
          Invite User
        </Button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-disabled)]" />
          <Input
            placeholder={t("admin.user_list.search_placeholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">{t("admin.user_list.all_roles")}</option>
          <option value="admin">Admin</option>
          <option value="manager">Manager</option>
          <option value="user">User</option>
        </select>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-[var(--text-muted)]">
          <Spinner /> {t("admin.user_list.loading")}
        </div>
      ) : !users?.length ? (
        <Card className="p-6 text-center text-[var(--text-muted)]">
          <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>{t("admin.user_list.no_users")}</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b text-right">
                <th className="p-2 font-medium">{t("admin.user_list.name")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.email")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.role")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.tenant")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.status")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.last_login")}</th>
                <th className="p-2 font-medium">{t("admin.user_list.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user: AdminUser) => (
                <tr
                  key={user.id}
                  className="border-b hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-primary)]"
                >
                  <td className="p-2 font-medium" data-label={t("admin.user_list.name")}>
                    <div>{user.full_name}</div>
                    {user.full_name_ar && user.full_name_ar !== user.full_name && (
                      <div className="text-xs text-[var(--text-muted)]">{user.full_name_ar}</div>
                    )}
                  </td>
                  <td className="p-2 text-xs" data-label={t("admin.user_list.email")}>
                    {user.email}
                  </td>
                  <td className="p-2" data-label={t("admin.user_list.role")}>
                    <Badge
                      variant={
                        user.role === "admin"
                          ? "success"
                          : user.role === "manager"
                            ? "warning"
                            : "default"
                      }
                    >
                      {user.role}
                    </Badge>
                  </td>
                  <td
                    className="p-2 text-xs text-[var(--text-muted)]"
                    data-label={t("admin.user_list.tenant")}
                  >
                    {user.tenant_name}
                  </td>
                  <td className="p-2" data-label={t("admin.user_list.status")}>
                    {user.is_active ? (
                      <span className="flex items-center gap-1 text-success-600">
                        <CheckCircle className="h-3.5 w-3.5" /> {t("admin.user_list.active")}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600">
                        <XCircle className="h-3.5 w-3.5" /> {t("admin.user_list.inactive")}
                      </span>
                    )}
                  </td>
                  <td
                    className="p-2 text-xs text-[var(--text-muted)]"
                    data-label={t("admin.user_list.last_login")}
                  >
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleDateString("ar-SA")
                      : "-"}
                  </td>
                  <td className="p-2" data-label={t("admin.user_list.actions")}>
                    {user.is_active && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeactivate(user.id)}
                        disabled={deactivateMutation.isPending}
                      >
                        <UserX className="h-4 w-4 ml-1" />
                        {t("admin.user_list.deactivate")}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={inviteOpen} onOpenChange={handleInviteOpenChange}>
        <ModalContent data-testid="admin-invite-user-modal">
          <ModalHeader>Invite User</ModalHeader>
          <ModalBody>
            {inviteResult ? (
              <div className="space-y-3 text-sm" data-testid="admin-invite-result">
                <p>{inviteResult.message}</p>
                <p className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
                  Email delivery: <code>{inviteResult.email_delivery}</code> — credentials were not
                  emailed. Share them out of band.
                </p>
                {inviteResult.temporary_password ? (
                  <div>
                    <label className="block text-xs text-[var(--text-muted)] mb-1">
                      Temporary password (copy now)
                    </label>
                    <Input
                      readOnly
                      value={inviteResult.temporary_password}
                      data-testid="admin-invite-temp-password"
                      className="font-mono"
                    />
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="space-y-4">
                {inviteError ? (
                  <p
                    className="rounded border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-900 dark:border-danger-800 dark:bg-danger-950/30 dark:text-danger-100"
                    data-testid="admin-invite-error"
                    role="alert"
                  >
                    {inviteError}
                  </p>
                ) : null}
                <div>
                  <label
                    htmlFor="invite-email"
                    className="block text-xs text-[var(--text-muted)] mb-1"
                  >
                    Email
                  </label>
                  <Input
                    id="invite-email"
                    type="email"
                    autoComplete="off"
                    value={inviteEmail}
                    onChange={(e) => {
                      setInviteEmail(e.target.value);
                      if (inviteError) setInviteError(null);
                    }}
                    placeholder="user@example.com"
                    data-testid="admin-invite-email"
                  />
                </div>
                <div>
                  <label
                    htmlFor="invite-role"
                    className="block text-xs text-[var(--text-muted)] mb-1"
                  >
                    Role
                  </label>
                  <select
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full border rounded px-3 py-2 text-sm bg-transparent"
                    data-testid="admin-invite-role"
                  >
                    <option value="user">User</option>
                    <option value="manager">Manager</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            {inviteResult ? (
              <Button onClick={() => handleInviteOpenChange(false)}>Done</Button>
            ) : (
              <>
                <Button
                  variant="ghost"
                  onClick={() => handleInviteOpenChange(false)}
                  disabled={inviteSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleInviteSubmit}
                  disabled={inviteSubmitting}
                  data-testid="admin-invite-submit"
                >
                  {inviteSubmitting ? "Creating…" : "Create invite"}
                </Button>
              </>
            )}
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
