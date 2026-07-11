"use client"

import { useState } from "react"
import { Input, Button, Badge, Card, cn, Spinner } from "@salesos/ui"
import { Search, Plus, XCircle, CheckCircle, RefreshCw } from "lucide-react"
import { useAdminTenants, useCreateAdminTenant, useUpdateAdminTenant, useDeleteAdminTenant } from "@/lib/hooks/adminQueries"
import { AdminTenantListItem } from "@/lib/api"

export function TenantList() {
  const [search, setSearch] = useState("")
  const [planFilter, setPlanFilter] = useState("")
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createSlug, setCreateSlug] = useState("")
  const { data: tenants, isLoading } = useAdminTenants({ search: search || undefined, plan: planFilter || undefined })
  const createMutation = useCreateAdminTenant()
  const deleteMutation = useDeleteAdminTenant()

  const handleCreate = async () => {
    if (!createName || !createSlug) return
    await createMutation.mutateAsync({ name: createName, slug: createSlug })
    setShowCreate(false)
    setCreateName("")
    setCreateSlug("")
  }

  const handleToggleActive = (id: string, current: boolean) => {
    const mutation = useUpdateAdminTenant(id)
    mutation.mutate({ is_active: !current })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">إدارة العملاء</h2>
        <Button onClick={() => setShowCreate(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          عميل جديد
        </Button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="بحث عن عميل..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9"
          />
        </div>
        <select
          value={planFilter}
          onChange={(e) => setPlanFilter(e.target.value)}
          className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value="">كل الباقات</option>
          <option value="free">Free</option>
          <option value="starter">Starter</option>
          <option value="growth">Growth</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>

      {showCreate && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">عميل جديد</h3>
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="اسم العميل" value={createName} onChange={(e) => setCreateName(e.target.value)} />
            <Input placeholder="المعرف (slug)" value={createSlug} onChange={(e) => setCreateSlug(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={createMutation.isPending}>إنشاء</Button>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>إلغاء</Button>
          </div>
        </Card>
      )}

      {isLoading ? (
        <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
      ) : !tenants?.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <Building2Icon className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا يوجد عملاء</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-neutral-700 text-right">
                <th className="p-2 font-medium">الاسم</th>
                <th className="p-2 font-medium">المعرف</th>
                <th className="p-2 font-medium">الباقة</th>
                <th className="p-2 font-medium">المستخدمين</th>
                <th className="p-2 font-medium">الحالة</th>
                <th className="p-2 font-medium">تاريخ الإنشاء</th>
                <th className="p-2 font-medium">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant: AdminTenantListItem) => (
                <tr key={tenant.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                  <td className="p-2 font-medium" data-label="الاسم">{tenant.name}</td>
                  <td className="p-2 text-xs text-neutral-500 font-mono" data-label="المعرف">{tenant.slug}</td>
                  <td className="p-2" data-label="الباقة">
                    <Badge variant={tenant.plan === "enterprise" ? "success" : tenant.plan === "free" ? "default" : "warning"}>
                      {tenant.plan}
                    </Badge>
                  </td>
                  <td className="p-2" data-label="المستخدمين">{tenant.user_count}</td>
                  <td className="p-2" data-label="الحالة">
                    {tenant.is_active ? (
                      <span className="flex items-center gap-1 text-success-600"><CheckCircle className="h-3.5 w-3.5" /> نشط</span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600"><XCircle className="h-3.5 w-3.5" /> موقوف</span>
                    )}
                  </td>
                  <td className="p-2 text-xs text-neutral-500" data-label="تاريخ الإنشاء">
                    {new Date(tenant.created_at).toLocaleDateString("ar-SA")}
                  </td>
                  <td className="p-2" data-label="إجراءات">
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => handleToggleActive(tenant.id, tenant.is_active)}>
                        {tenant.is_active ? "إيقاف" : "تفعيل"}
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
  )
}

function Building2Icon(props: { className?: string }) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18M6 22H4m2 0h12m0 0h2M6 7h2m-2 4h2m-2 4h2m6-8h2m-2 4h2m-2 4h2" />
    </svg>
  )
}
