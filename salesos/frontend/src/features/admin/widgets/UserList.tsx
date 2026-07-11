"use client"

import { useState } from "react"
import { Input, Button, Badge, Card, cn, Spinner } from "@salesos/ui"
import { Search, Shield, UserX, CheckCircle, XCircle } from "lucide-react"
import { useAdminUsers, useDeactivateAdminUser } from "@/lib/hooks/adminQueries"
import { AdminUser } from "@/lib/api"

export function UserList() {
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState("")
  const { data: users, isLoading } = useAdminUsers({ search: search || undefined, role: roleFilter || undefined })
  const deactivateMutation = useDeactivateAdminUser()

  const handleDeactivate = async (id: string) => {
    await deactivateMutation.mutateAsync(id)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">إدارة المستخدمين</h2>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="بحث عن مستخدم..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value="">كل الأدوار</option>
          <option value="admin">Admin</option>
          <option value="manager">Manager</option>
          <option value="user">User</option>
        </select>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
      ) : !users?.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا يوجد مستخدمين</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-neutral-700 text-right">
                <th className="p-2 font-medium">الاسم</th>
                <th className="p-2 font-medium">البريد</th>
                <th className="p-2 font-medium">الدور</th>
                <th className="p-2 font-medium">العميل</th>
                <th className="p-2 font-medium">الحالة</th>
                <th className="p-2 font-medium">آخر دخول</th>
                <th className="p-2 font-medium">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user: AdminUser) => (
                <tr key={user.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                  <td className="p-2 font-medium" data-label="الاسم">
                    <div>{user.full_name}</div>
                    {user.full_name_ar && user.full_name_ar !== user.full_name && (
                      <div className="text-xs text-neutral-500">{user.full_name_ar}</div>
                    )}
                  </td>
                  <td className="p-2 text-xs" data-label="البريد">{user.email}</td>
                  <td className="p-2" data-label="الدور">
                    <Badge variant={user.role === "admin" ? "success" : user.role === "manager" ? "warning" : "default"}>
                      {user.role}
                    </Badge>
                  </td>
                  <td className="p-2 text-xs text-neutral-500" data-label="العميل">{user.tenant_name}</td>
                  <td className="p-2" data-label="الحالة">
                    {user.is_active ? (
                      <span className="flex items-center gap-1 text-success-600"><CheckCircle className="h-3.5 w-3.5" /> نشط</span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600"><XCircle className="h-3.5 w-3.5" /> غير نشط</span>
                    )}
                  </td>
                  <td className="p-2 text-xs text-neutral-500" data-label="آخر دخول">
                    {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString("ar-SA") : "-"}
                  </td>
                  <td className="p-2" data-label="إجراءات">
                    {user.is_active && (
                      <Button size="sm" variant="ghost" onClick={() => handleDeactivate(user.id)} disabled={deactivateMutation.isPending}>
                        <UserX className="h-4 w-4 ml-1" />
                        تعطيل
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
  )
}
