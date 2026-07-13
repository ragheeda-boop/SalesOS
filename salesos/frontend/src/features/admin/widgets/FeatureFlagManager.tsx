"use client"

import { useState } from "react"
import { Button, Badge, Card, Spinner } from "@salesos/ui"
import { Plus, ToggleLeft, ToggleRight } from "lucide-react"
import { useAdminFeatureFlags, useCreateAdminFeatureFlag, useAdminFlagTenants, useToggleAdminFlagForTenant } from "@/lib/hooks/adminQueries"
import { AdminFeatureFlag } from "@/lib/api"

export function FeatureFlagManager() {
  const { data: flags, isLoading } = useAdminFeatureFlags()
  const [showCreate, setShowCreate] = useState(false)
  const [createKey, setCreateKey] = useState("")
  const [createName, setCreateName] = useState("")
  const [selectedFlag, setSelectedFlag] = useState<string | null>(null)
  const createMutation = useCreateAdminFeatureFlag()

  const handleCreate = async () => {
    if (!createKey || !createName) return
    await createMutation.mutateAsync({ key: createKey, name: createName })
    setShowCreate(false)
    setCreateKey("")
    setCreateName("")
  }

  if (isLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">الميزات التجريبية</h2>
        <Button onClick={() => setShowCreate(true)} className="gap-2"><Plus className="h-4 w-4" />ميزة جديدة</Button>
      </div>

      {showCreate && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">ميزة جديدة</h3>
          <div className="grid grid-cols-2 gap-3">
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" placeholder="المفتاح (key)" value={createKey} onChange={(e) => setCreateKey(e.target.value)} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" placeholder="الاسم" value={createName} onChange={(e) => setCreateName(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={createMutation.isPending}>إنشاء</Button>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>إلغاء</Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-4">
          <h3 className="font-semibold mb-3">جميع الميزات ({flags?.length || 0})</h3>
          <div className="space-y-2">
            {flags?.map((flag: AdminFeatureFlag) => (
              <button
                key={flag.id}
                onClick={() => setSelectedFlag(selectedFlag === flag.id ? null : flag.id)}
                className={`w-full flex items-center justify-between p-3 rounded-lg border text-right transition ${
                  selectedFlag === flag.id ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5" : "border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                }`}
              >
                <div>
                  <p className="font-medium text-sm">{flag.name}</p>
                  <p className="text-xs text-neutral-500 font-mono">{flag.key}</p>
                  {flag.description && <p className="text-xs text-neutral-400 mt-0.5">{flag.description}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={flag.enabled ? "success" : "default"}>{flag.enabled ? "مفعل" : "معطل"}</Badge>
                  {flag.is_global && <Badge variant="default">عام</Badge>}
                </div>
              </button>
            ))}
          </div>
        </Card>

        <div>
          {selectedFlag ? (
            <FlagTenantManager flagId={selectedFlag} />
          ) : (
            <Card className="p-6 text-center text-neutral-500">
              <ToggleLeft className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>اختر ميزة لإدارة تفعيلها لكل عميل</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

function FlagTenantManager({ flagId }: { flagId: string }) {
  const { data: tenants, isLoading } = useAdminFlagTenants(flagId)
  const toggleMutation = useToggleAdminFlagForTenant(flagId)

  if (isLoading) return <Card className="p-6 text-center"><Spinner /></Card>

  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">تفعيل الميزة لكل عميل</h3>
      {!tenants?.length ? (
        <p className="text-sm text-neutral-500 text-center py-4">لا توجد تجاوزات لهذه الميزة</p>
      ) : (
        <div className="space-y-2">
          {tenants.map((t: { tenant_name: string; tenant_id: string; enabled: boolean }) => (
            <div key={t.tenant_id} className="flex items-center justify-between p-2 rounded-lg border dark:border-neutral-700">
              <span className="text-sm">{t.tenant_name}</span>
              <button
                onClick={() => toggleMutation.mutate({ tenantId: t.tenant_id, enabled: !t.enabled })}
                className={`px-3 py-1 rounded text-xs font-medium transition ${
                  t.enabled ? "bg-success-100 text-success-700 dark:bg-success-900/30" : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800"
                }`}
              >
                {t.enabled ? "مفعل" : "معطل"}
              </button>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
