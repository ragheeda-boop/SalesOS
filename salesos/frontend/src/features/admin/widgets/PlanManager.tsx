"use client"

import { useState } from "react"
import { Button, Badge, Card, Spinner } from "@salesos/ui"
import { Plus, Edit3 } from "lucide-react"
import { useAdminPlans, useAdminLicenses, useCreateAdminPlan, useCreateAdminLicense } from "@/lib/hooks/adminQueries"
import { AdminPlan, AdminLicense } from "@/lib/api"

export function PlanManager() {
  const { data: plans, isLoading: plansLoading } = useAdminPlans()
  const { data: licenses, isLoading: licensesLoading } = useAdminLicenses()
  const [showCreatePlan, setShowCreatePlan] = useState(false)
  const [showCreateLicense, setShowCreateLicense] = useState(false)
  const [planForm, setPlanForm] = useState({ name: "", tier: "free" as const, price_monthly: 0, max_users: 1, max_storage_mb: 100, max_api_calls: 1000, features: "" })
  const [licenseForm, setLicenseForm] = useState({ tenant_id: "", plan_id: "" })

  const createPlanMutation = useCreateAdminPlan()
  const createLicenseMutation = useCreateAdminLicense()

  const handleCreatePlan = async () => {
    await createPlanMutation.mutateAsync({
      ...planForm,
      features: planForm.features.split(",").map((f: string) => f.trim()).filter(Boolean),
    })
    setShowCreatePlan(false)
    setPlanForm({ name: "", tier: "free", price_monthly: 0, max_users: 1, max_storage_mb: 100, max_api_calls: 1000, features: "" })
  }

  if (plansLoading || licensesLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">الباقات والتراخيص</h2>
        <div className="flex gap-2">
          <Button onClick={() => setShowCreateLicense(true)} className="gap-2"><Plus className="h-4 w-4" />ترخيص جديد</Button>
          <Button onClick={() => setShowCreatePlan(true)} className="gap-2"><Plus className="h-4 w-4" />باقة جديدة</Button>
        </div>
      </div>

      {showCreatePlan && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">باقة جديدة</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" placeholder="الاسم" value={planForm.name} onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })} />
            <select className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" value={planForm.tier} onChange={(e) => setPlanForm({ ...planForm, tier: e.target.value as "free" | "starter" | "growth" | "enterprise" })}>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="growth">Growth</option>
              <option value="enterprise">Enterprise</option>
            </select>
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" type="number" placeholder="السعر الشهري" value={planForm.price_monthly} onChange={(e) => setPlanForm({ ...planForm, price_monthly: Number(e.target.value) })} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" type="number" placeholder="الحد الأقصى للمستخدمين" value={planForm.max_users} onChange={(e) => setPlanForm({ ...planForm, max_users: Number(e.target.value) })} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" type="number" placeholder="المساحة (MB)" value={planForm.max_storage_mb} onChange={(e) => setPlanForm({ ...planForm, max_storage_mb: Number(e.target.value) })} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" type="number" placeholder="الاستدعاءات" value={planForm.max_api_calls} onChange={(e) => setPlanForm({ ...planForm, max_api_calls: Number(e.target.value) })} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700 col-span-full" placeholder="الميزات (مفصولة بفاصلة)" value={planForm.features} onChange={(e) => setPlanForm({ ...planForm, features: e.target.value })} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreatePlan} disabled={createPlanMutation.isPending}>إنشاء</Button>
            <Button variant="ghost" onClick={() => setShowCreatePlan(false)}>إلغاء</Button>
          </div>
        </Card>
      )}

      {showCreateLicense && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">ترخيص جديد</h3>
          <div className="grid grid-cols-2 gap-3">
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" placeholder="معرف العميل (tenant_id)" value={licenseForm.tenant_id} onChange={(e) => setLicenseForm({ ...licenseForm, tenant_id: e.target.value })} />
            <input className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700" placeholder="معرف الباقة (plan_id)" value={licenseForm.plan_id} onChange={(e) => setLicenseForm({ ...licenseForm, plan_id: e.target.value })} />
          </div>
          <div className="flex gap-2">
            <Button onClick={async () => { await createLicenseMutation.mutateAsync({ tenant_id: licenseForm.tenant_id, plan_id: licenseForm.plan_id }); setShowCreateLicense(false) }} disabled={createLicenseMutation.isPending}>إنشاء</Button>
            <Button variant="ghost" onClick={() => setShowCreateLicense(false)}>إلغاء</Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-4">
          <h3 className="font-semibold mb-3">الباقات ({plans?.length || 0})</h3>
          <div className="space-y-3">
            {plans?.map((plan: AdminPlan) => (
              <div key={plan.id} className="border dark:border-neutral-700 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{plan.name}</span>
                  <Badge variant={plan.tier === "enterprise" ? "success" : plan.tier === "free" ? "default" : "warning"}>{plan.tier}</Badge>
                </div>
                <div className="text-sm text-neutral-500 space-y-1">
                  <p>SAR {plan.price_monthly}/شهرياً | SAR {plan.price_yearly}/سنوياً</p>
                  <p>{plan.max_users} مستخدم | {plan.max_storage_mb} MB | {plan.max_api_calls.toLocaleString()} استدعاء</p>
                  {plan.features?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {plan.features.map((f: string) => <Badge key={f} variant="default">{f}</Badge>)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-semibold mb-3">التراخيص ({licenses?.length || 0})</h3>
          <div className="space-y-3">
            {licenses?.map((lic: AdminLicense) => (
              <div key={lic.id} className="border dark:border-neutral-700 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{lic.tenant_name}</span>
                  <Badge variant={lic.is_active ? "success" : "default"}>{lic.is_active ? "نشط" : "غير نشط"}</Badge>
                </div>
                <p className="text-xs text-neutral-500">{lic.plan_name} ({lic.tier})</p>
                {lic.ends_at && <p className="text-xs text-neutral-400">ينتهي: {new Date(lic.ends_at).toLocaleDateString("ar-SA")}</p>}
              </div>
            ))}
            {(!licenses || licenses.length === 0) && (
              <p className="text-sm text-neutral-500 text-center py-4">لا توجد تراخيص</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
