"use client";

import { useState } from "react";
import { Input, Button, Badge, Card, Spinner } from "@salesos/ui";
import { Search, Shield, UserX, CheckCircle, XCircle } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import {
  useAdminUsers,
  useDeactivateAdminUser,
} from "@/lib/hooks/adminQueries";
import { AdminUser } from "@/lib/api";

export function UserList() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const { data: users, isLoading } = useAdminUsers({
    search: search || undefined,
    role: roleFilter || undefined,
  });
  const deactivateMutation = useDeactivateAdminUser();

  const handleDeactivate = async (id: string) => {
    await deactivateMutation.mutateAsync(id);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">{t("admin.user_list.title")}</h2>

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
                <th className="p-2 font-medium">
                  {t("admin.user_list.email")}
                </th>
                <th className="p-2 font-medium">{t("admin.user_list.role")}</th>
                <th className="p-2 font-medium">
                  {t("admin.user_list.tenant")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.user_list.status")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.user_list.last_login")}
                </th>
                <th className="p-2 font-medium">
                  {t("admin.user_list.actions")}
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user: AdminUser) => (
                <tr
                  key={user.id}
                  className="border-b hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-primary)]"
                >
                  <td
                    className="p-2 font-medium"
                    data-label={t("admin.user_list.name")}
                  >
                    <div>{user.full_name}</div>
                    {user.full_name_ar &&
                      user.full_name_ar !== user.full_name && (
                        <div className="text-xs text-[var(--text-muted)]">
                          {user.full_name_ar}
                        </div>
                      )}
                  </td>
                  <td
                    className="p-2 text-xs"
                    data-label={t("admin.user_list.email")}
                  >
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
                        <CheckCircle className="h-3.5 w-3.5" />{" "}
                        {t("admin.user_list.active")}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600">
                        <XCircle className="h-3.5 w-3.5" />{" "}
                        {t("admin.user_list.inactive")}
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
    </div>
  );
}
