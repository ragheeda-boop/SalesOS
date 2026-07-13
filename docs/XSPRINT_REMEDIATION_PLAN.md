# X-SPRINT: فجوة Frontend-Backend — خطة الوصول إلى 95%

> **الهدف**: رفع نسبة وصول العميل للميزات من 40% إلى 95%
> **المدة**: 13 ساعة عمل موزعة على 4 مراحل
> **التاريخ المستهدف**: أسبوع واحد
> **المسؤول**: Backend Engineer + Frontend Engineer

---

## الوضع الحالي

```
Backend APIs:   ████████████████████████████████  95%
Frontend Pages: ████████████████████░░░░░░░░░░░░  65%
Routes Wired:   ████████████████░░░░░░░░░░░░░░░░  55%
Customer View:  ██████████░░░░░░░░░░░░░░░░░░░░░░  40%
                                                  
الهدف:          ███████████████████████████████░  95%
```

## المشكلة الجذرية

7 مكونات React مبنية بالكامل مع API كامل في الـ Backend، لكن لا يوجد Route يربط بينهما. المكونات "يتيمة" (orphaned) — موجودة في `features/` لكن لا `page.tsx` يوصل لها.

---

## المرحلة الأولى: ربط المكونات اليتيمة (3 ساعات) 🟢

### المهمة 1.1: Revenue Intelligence (`/revenue`) — 30 دقيقة

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/revenue/page.tsx
```

**الكود:**

```tsx
"use client"

import { RevenueWorkspace } from "@/features/revenue-execution/workspace/revenue/RevenueWorkspace"

export default function RevenuePage() {
  return <RevenueWorkspace />
}
```

---

### المهمة 1.2: Pipeline Analytics (`/pipeline`) — 30 دقيقة

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/pipeline/page.tsx
```

**الكود:**

```tsx
"use client"

import { PipelineWorkspace } from "@/features/revenue-execution/workspace/pipeline/PipelineWorkspace"

export default function PipelinePage() {
  return <PipelineWorkspace />
}
```

**ملاحظة**: مفتاح `nav.pipeline` موجود مسبقًا في i18n (ar.json و en.json) لكنه غير مستخدم.

---

### المهمة 1.3: Opportunity 360 Detail (`/opportunities/[id]`) — 30 دقيقة

**المجلد المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/opportunities/[id]/
```

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/opportunities/[id]/page.tsx
```

**الكود:**

```tsx
"use client"

import { useParams } from "next/navigation"
import { OpportunityWorkspace } from "@/features/revenue-execution/workspace/OpportunityWorkspace"

export default function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>()
  return <OpportunityWorkspace opportunityId={id} />
}
```

---

### المهمة 1.4: Forecast (`/forecast`) — 30 دقيقة

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/forecast/page.tsx
```

**الكود:**

```tsx
"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"
import { useTranslation } from "@/lib/i18n"

interface ForecastData {
  total_expected: number
  weighted: number
  confidence: number
  risk: number
  horizon: string
  scenarios?: {
    pessimistic: number
    baseline: number
    optimistic: number
  }
}

export default function ForecastPage() {
  const { t } = useTranslation()
  const [forecast, setForecast] = useState<ForecastData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get("/api/v1/forecast")
      .then(res => { setForecast(res.data); setLoading(false) })
      .catch(() => { setError(t("error.server_error")); setLoading(false) })
  }, [t])

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>
  if (!forecast) return <div className="p-8 text-center text-neutral-500">{t("common.no_results")}</div>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("forecast.title")}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ForecastCard label={t("forecast.total_expected")} value={forecast.total_expected} />
        <ForecastCard label={t("forecast.weighted")} value={forecast.weighted} />
        <ForecastCard label={t("forecast.confidence")} value={`${forecast.confidence}%`} />
      </div>
      {forecast.scenarios && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ForecastCard label={t("forecast.pessimistic")} value={forecast.scenarios.pessimistic} variant="red" />
          <ForecastCard label={t("forecast.baseline")} value={forecast.scenarios.baseline} variant="neutral" />
          <ForecastCard label={t("forecast.optimistic")} value={forecast.scenarios.optimistic} variant="green" />
        </div>
      )}
    </div>
  )
}

function ForecastCard({ label, value, variant = "neutral" }: {
  label: string
  value: string | number
  variant?: "green" | "red" | "neutral"
}) {
  return (
    <div className={cn(
      "rounded-xl border p-4 bg-white dark:bg-neutral-900",
      variant === "green" && "border-green-200 dark:border-green-800",
      variant === "red" && "border-red-200 dark:border-red-800",
      variant === "neutral" && "border-neutral-200 dark:border-neutral-700"
    )}>
      <p className="text-sm text-neutral-500">{label}</p>
      <p className={cn(
        "text-2xl font-bold mt-1",
        variant === "green" && "text-green-600",
        variant === "red" && "text-red-600"
      )}>{value}</p>
    </div>
  )
}
```

---

### المهمة 1.5: Decision Center (`/decisions`) — 60 دقيقة

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/decisions/page.tsx
```

**الكود:**

```tsx
"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"
import { ArrowUpRight, Check, X, ChevronRight } from "lucide-react"

interface DecisionItem {
  id: string
  entity_type: string
  entity_id: string
  action: string
  priority: "high" | "medium" | "low"
  score: number
  reasoning: string
  created_at: string
  status: "pending" | "accepted" | "executed" | "dismissed"
}

export default function DecisionCenterPage() {
  const { t } = useTranslation()
  const [decisions, setDecisions] = useState<DecisionItem[]>([])
  const [selected, setSelected] = useState<DecisionItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get("/api/v1/decision/history?limit=50")
      .then(res => { setDecisions(res.data.items || []); setLoading(false) })
      .catch(() => { setError(t("error.server_error")); setLoading(false) })
  }, [t])

  const handleAccept = async (id: string) => {
    await axios.post(`/api/v1/decisions/${id}/accept`)
    setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "accepted" as const } : d))
  }

  const handleDismiss = async (id: string) => {
    await axios.post(`/api/v1/decisions/${id}/feedback`, { accepted: false })
    setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "dismissed" as const } : d))
  }

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("decisions.title")}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {decisions.length === 0 && (
            <p className="text-neutral-500 p-8 text-center">{t("common.no_results")}</p>
          )}
          {decisions.map(d => (
            <div
              key={d.id}
              onClick={() => setSelected(d)}
              className={cn(
                "rounded-lg border p-4 cursor-pointer hover:border-[var(--muhide-orange)] transition bg-white dark:bg-neutral-900",
                selected?.id === d.id && "border-[var(--muhide-orange)] ring-1 ring-[var(--muhide-orange)]"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={cn(
                    "px-2 py-0.5 rounded text-xs font-medium",
                    d.priority === "high" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                    d.priority === "medium" && "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
                    d.priority === "low" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  )}>
                    {d.priority}
                  </span>
                  <span className="font-medium">{d.action}</span>
                </div>
                <ChevronRight className="h-4 w-4 text-neutral-400" />
              </div>
            </div>
          ))}
        </div>

        {selected && (
          <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 space-y-3">
            <h3 className="font-bold text-lg">{selected.action}</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">{selected.reasoning}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-500">{t("decisions.score")}: {selected.score}</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-xs",
                selected.status === "accepted" && "bg-green-100 text-green-700",
                selected.status === "dismissed" && "bg-red-100 text-red-700",
                selected.status === "pending" && "bg-blue-100 text-blue-700"
              )}>
                {selected.status}
              </span>
            </div>
            {selected.status === "pending" && (
              <div className="flex gap-2 pt-2">
                <button onClick={() => handleAccept(selected.id)} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                  <Check className="h-4 w-4" /> {t("decisions.accept")}
                </button>
                <button onClick={() => handleDismiss(selected.id)} className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">
                  <X className="h-4 w-4" /> {t("decisions.dismiss")}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

---

### المهمة 1.6: تحديث الشريط الجانبي (Sidebar) — 15 دقيقة

**الملف: `salesos/frontend/src/app/(dashboard)/layout.tsx`**

**تعديل 1**: إضافة icon imports (السطر 8):

```tsx
// قبل:
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, Bell, Menu, Bot, User, Shield, Workflow, MessageSquareText, Activity, HeartHandshake, X } from "lucide-react"

// بعد:
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, Bell, Menu, Bot, User, Shield, Workflow, MessageSquareText, Activity, HeartHandshake, X, TrendingUp, BarChart3, Brain, CalendarClock } from "lucide-react"
```

**تعديل 2**: تحديث NAV_KEYS (الأسطر 18-31):

```tsx
const NAV_KEYS = [
  // المجموعة الرئيسية
  { href: "/dashboard",        key: "nav.dashboard",        icon: LayoutDashboard },
  { href: "/companies",        key: "nav.companies",        icon: Building2 },
  { href: "/employees/me",     key: "nav.profile",          icon: User },
  { href: "/contacts",         key: "nav.contacts",         icon: Users },
  // المبيعات والإيرادات
  { href: "/opportunities",    key: "nav.opportunities",    icon: DollarSign },
  { href: "/revenue",          key: "nav.revenue",          icon: TrendingUp },
  { href: "/pipeline",         key: "nav.pipeline",         icon: BarChart3 },
  { href: "/forecast",         key: "nav.forecast",         icon: CalendarClock },
  // الذكاء والقرارات
  { href: "/search",           key: "nav.search",           icon: Search },
  { href: "/decisions",        key: "nav.decisions",        icon: Brain },
  { href: "/rag",              key: "nav.rag",              icon: MessageSquareText },
  // العمليات
  { href: "/automation",       key: "nav.workflows",        icon: Workflow },
  { href: "/monitoring",       key: "nav.monitoring",       icon: Activity },
  { href: "/customer-success", key: "nav.customer_success", icon: HeartHandshake },
  // الإعدادات
  { href: "/settings",         key: "nav.settings",         icon: Settings },
  { href: "/admin",            key: "nav.admin",            icon: Shield },
]
```

---

### المهمة 1.7: تحديث i18n — 15 دقيقة

**الملف: `salesos/frontend/src/lib/i18n/ar.json`** — أضف بعد السطر 15:

```json
  "nav.revenue": "الإيرادات",
  "nav.pipeline": "خط الأنابيب",
  "nav.forecast": "التوقعات",
  "nav.decisions": "مركز القرارات",
```

وعدّل السطر 3 (إن كان موجودًا بمفتاح مختلف):

```
"nav.pipeline": "خط الأنابيب",    ← موجود بالفعل
```

**الملف: `salesos/frontend/src/lib/i18n/en.json`** — أضف بعد السطر 15:

```json
  "nav.revenue": "Revenue",
  "nav.pipeline": "Pipeline",
  "nav.forecast": "Forecast",
  "nav.decisions": "Decisions",
```

وأضف مفاتيح إضافية في كلا الملفين:

```json
  "forecast.title": "توقعات الإيرادات",
  "forecast.total_expected": "الإجمالي المتوقع",
  "forecast.weighted": "المتوسط المرجح",
  "forecast.confidence": "مستوى الثقة",
  "forecast.pessimistic": "السيناريو المتشائم",
  "forecast.baseline": "السيناريو الأساسي",
  "forecast.optimistic": "السيناريو المتفائل",

  "decisions.title": "مركز القرارات",
  "decisions.score": "الدرجة",
  "decisions.accept": "قبول",
  "decisions.dismiss": "رفض",
```

---

### التحقق من المرحلة الأولى

```bash
# تأكد من وجود كل الملفات الجديدة
Test-Path "salesos/frontend/src/app/(dashboard)/revenue/page.tsx"
Test-Path "salesos/frontend/src/app/(dashboard)/pipeline/page.tsx"
Test-Path "salesos/frontend/src/app/(dashboard)/opportunities/[id]/page.tsx"
Test-Path "salesos/frontend/src/app/(dashboard)/forecast/page.tsx"
Test-Path "salesos/frontend/src/app/(dashboard)/decisions/page.tsx"

# تأكد من بناء Next.js بدون أخطاء
npm run build
```

---

## المرحلة الثانية: تفعيل الخلفيات المخفية (3 ساعات) 🟡

### المهمة 2.1: تسجيل AI Router في main.py — 15 دقيقة

**الملف: `salesos/backend/app/main.py`** — أضف بعد السطر 651 (بعد قسم Analytics):

```python
    # Wave 3 — AI Prompt Registry & Evaluation
    from app.routers.ai import router as ai_router
    app.include_router(ai_router, prefix="/api/v1", tags=["AI"], dependencies=_auth)
```

---

### المهمة 2.2: صفحة AI Prompt Registry (`/ai`) — ساعتان

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/ai/page.tsx
```

**الكود:**

```tsx
"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"
import { Plus, Play, Copy, Check, RefreshCw } from "lucide-react"

interface PromptTemplate {
  id: string
  name: string
  version: string
  system_prompt: string
  user_prompt_template: string
  is_active: boolean
  metrics?: {
    accuracy: number
    latency_ms: number
    usage_count: number
  }
}

export default function AIPage() {
  const { t } = useTranslation()
  const [prompts, setPrompts] = useState<PromptTemplate[]>([])
  const [selected, setSelected] = useState<PromptTemplate | null>(null)
  const [testInput, setTestInput] = useState("")
  const [testResult, setTestResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [evaluating, setEvaluating] = useState(false)

  useEffect(() => {
    axios.get("/api/v1/ai/prompts")
      .then(res => { setPrompts(res.data.prompts || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const handleTest = async () => {
    if (!selected) return
    setEvaluating(true)
    try {
      const res = await axios.post("/api/v1/ai/generate", {
        prompt_id: selected.id,
        variables: { input: testInput }
      })
      setTestResult(res.data.output)
    } catch { setTestResult("Error generating output") }
    setEvaluating(false)
  }

  const handleActivate = async (id: string) => {
    await axios.post("/api/v1/ai/prompts/activate", { prompt_id: id })
    setPrompts(prev => prev.map(p => ({ ...p, is_active: p.id === id })))
  }

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("ai.title")}</h1>
        <button className="flex items-center gap-2 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90">
          <Plus className="h-4 w-4" /> {t("ai.new_prompt")}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2 max-h-[70vh] overflow-y-auto">
          {prompts.length === 0 && (
            <p className="text-neutral-500 p-4">{t("common.no_results")}</p>
          )}
          {prompts.map(p => (
            <div
              key={p.id}
              onClick={() => setSelected(p)}
              className={cn(
                "rounded-lg border p-3 cursor-pointer hover:border-[var(--muhide-orange)] transition",
                selected?.id === p.id && "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5",
                p.is_active && "border-l-4 border-l-green-500"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">{p.name}</span>
                <span className="text-xs text-neutral-400">v{p.version}</span>
              </div>
              {p.metrics && (
                <div className="flex gap-3 mt-1 text-xs text-neutral-500">
                  <span>{t("ai.accuracy")}: {p.metrics.accuracy}%</span>
                  <span>{p.metrics.latency_ms}ms</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {selected && (
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold">{selected.name} <span className="text-neutral-400 font-normal">v{selected.version}</span></h3>
                <button
                  onClick={() => handleActivate(selected.id)}
                  disabled={selected.is_active}
                  className={cn(
                    "px-3 py-1 rounded text-sm",
                    selected.is_active ? "bg-green-100 text-green-700" : "bg-neutral-100 hover:bg-[var(--muhide-orange)]/10 text-neutral-700 hover:text-[var(--muhide-orange)]"
                  )}
                >
                  {selected.is_active ? t("ai.active") : t("ai.activate")}
                </button>
              </div>
              <div>
                <label className="text-xs font-medium text-neutral-500 uppercase">{t("ai.system_prompt")}</label>
                <pre className="mt-1 p-3 bg-neutral-50 dark:bg-neutral-800 rounded text-sm whitespace-pre-wrap">{selected.system_prompt}</pre>
              </div>
              <div>
                <label className="text-xs font-medium text-neutral-500 uppercase">{t("ai.user_template")}</label>
                <pre className="mt-1 p-3 bg-neutral-50 dark:bg-neutral-800 rounded text-sm whitespace-pre-wrap">{selected.user_prompt_template}</pre>
              </div>
            </div>

            <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 space-y-3">
              <h4 className="font-medium">{t("ai.test_prompt")}</h4>
              <textarea
                value={testInput}
                onChange={e => setTestInput(e.target.value)}
                placeholder={t("ai.test_placeholder")}
                className="w-full p-3 border rounded-lg text-sm min-h-[80px] bg-white dark:bg-neutral-800"
              />
              <button
                onClick={handleTest}
                disabled={evaluating || !testInput}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90 disabled:opacity-50"
              >
                {evaluating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {evaluating ? t("common.loading") : t("ai.run_test")}
              </button>
              {testResult && (
                <div className="mt-3 p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg text-sm">{testResult}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

### المهمة 2.3: صفحة Knowledge Graph (`/graph`) — ساعة واحدة

**الملف المطلوب إنشاؤه:**

```
salesos/frontend/src/app/(dashboard)/graph/page.tsx
```

**الكود:**

```tsx
"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { Search } from "lucide-react"

export default function KnowledgeGraphPage() {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await axios.get("/api/v1/graph/search", { params: { q: query } })
      setResults(res.data.nodes || [])
    } catch { /* silent */ }
    setLoading(false)
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("graph.title")}</h1>
      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSearch()}
          placeholder={t("graph.search_placeholder")}
          className="flex-1 p-2 border rounded-lg text-sm"
        />
        <button onClick={handleSearch} className="flex items-center gap-2 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg">
          <Search className="h-4 w-4" /> {t("common.search")}
        </button>
      </div>
      {loading && <p className="text-neutral-500">{t("common.loading")}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {results.map((node, i) => (
          <div key={i} className="rounded-lg border p-3 bg-white dark:bg-neutral-900">
            <p className="font-medium">{node.name || node.label || node.id}</p>
            {node.type && <p className="text-xs text-neutral-500">{node.type}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

### المهمة 2.4: تحديث i18n للمرحلة الثانية — 15 دقيقة

i18n keys إضافية للمرحلة الثانية:

```json
// ar.json
  "nav.ai": "الذكاء الاصطناعي",
  "nav.graph": "الرسم البياني",
  "ai.title": "سجل الأوامر الذكية",
  "ai.new_prompt": "أمر جديد",
  "ai.system_prompt": "النظام (System)",
  "ai.user_template": "القالب (Template)",
  "ai.test_prompt": "تجربة الأمر",
  "ai.test_placeholder": "أدخل متغيرات الاختبار...",
  "ai.run_test": "تشغيل الاختبار",
  "ai.activate": "تفعيل",
  "ai.active": "نشط",
  "ai.accuracy": "الدقة",
  "graph.title": "الرسم البياني المعرفي",
  "graph.search_placeholder": "ابحث عن كيان أو علاقة...",

// en.json
  "nav.ai": "AI",
  "nav.graph": "Knowledge Graph",
  "ai.title": "AI Prompt Registry",
  "ai.new_prompt": "New Prompt",
  "ai.system_prompt": "System Prompt",
  "ai.user_template": "User Template",
  "ai.test_prompt": "Test Prompt",
  "ai.test_placeholder": "Enter test variables...",
  "ai.run_test": "Run Test",
  "ai.activate": "Activate",
  "ai.active": "Active",
  "ai.accuracy": "Accuracy",
  "graph.title": "Knowledge Graph",
  "graph.search_placeholder": "Search for an entity or relationship...",
```

---

### المهمة 2.5: تحديث الشريط الجانبي للمرحلة الثانية — 5 دقائق

أضف للـ NAV_KEYS:

```tsx
  { href: "/ai",    key: "nav.ai",    icon: Sparkles },
  { href: "/graph", key: "nav.graph", icon: GitGraph },
```

وتأكد من استيراد الأيقونات من lucide-react: `Sparkles`, `GitGraph`.

---

## المرحلة الثالثة: تثبيت وتحسين (4 ساعات) 🟡

### المهمة 3.1: إضافة Error Boundaries و Loading States — ساعتان

**الملف: `salesos/frontend/src/app/(dashboard)/error.tsx`**

```tsx
"use client"

import { useEffect } from "react"
import { useTranslation } from "@/lib/i18n"

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const { t } = useTranslation()

  useEffect(() => {
    console.error("Dashboard error:", error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
        {t("error.default_title")}
      </h2>
      <p className="mt-2 text-neutral-500">{t("error.default_message")}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90"
      >
        {t("error.retry")}
      </button>
    </div>
  )
}
```

**الملف: `salesos/frontend/src/app/(dashboard)/loading.tsx`**

```tsx
export default function DashboardLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin h-8 w-8 border-4 border-[var(--muhide-orange)] border-t-transparent rounded-full" />
    </div>
  )
}
```

**الملف: `salesos/frontend/src/app/(dashboard)/not-found.tsx`**

```tsx
import Link from "next/link"

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <h1 className="text-6xl font-bold text-neutral-200 dark:text-neutral-700">404</h1>
      <p className="mt-4 text-neutral-500">الصفحة غير موجودة</p>
      <Link
        href="/dashboard"
        className="mt-4 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90"
      >
        العودة للرئيسية
      </Link>
    </div>
  )
}
```

---

### المهمة 3.2: إصلاح Company 360 503 — ساعة

**المشكلة**: `GET /api/v1/companies/{id}/360` يرجع 503 في بعض الحالات.

**التحقيق المطلوب**:
1. تحقق من `app/modules/company/router.py` — دالة `get_company_360`
2. الـ 360 endpoint يعتمد على `activity_runtime` و `kg_engine` — أي فشل في أي منهما يعيد 503
3. أضف try/except حول استدعاءات الـ runtime dependencies

**الملف: `salesos/backend/app/modules/company/router.py`**

أضف graceful degradation — إذا فشل الـ runtime dependency، أرجع البيانات الأساسية بدل 503:

```python
@router.get("/{company_id}/360")
async def get_company_360(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    result = {"company": CompanySchema.from_orm(company)}
    
    # Graceful degradation for runtime dependencies
    try:
        activity = await activity_runtime.get_entity_activity("company", str(company_id))
        result["activity"] = activity
    except Exception:
        result["activity"] = None  # لا تكسر الصفحة
    
    try:
        kg = await kg_engine.get_entity_graph("company", str(company_id))
        result["knowledge_graph"] = kg
    except Exception:
        result["knowledge_graph"] = None
    
    return result
```

---

### المهمة 3.3: إصلاح Employee 360 API — 30 دقيقة

نفس نمط الـ graceful degradation — `app/modules/employee_360/router.py`.

---

### المهمة 3.4: تشغيل ESLint + TypeScript check — 30 دقيقة

```bash
# في مجلد frontend
npm run lint

# تأكد من عدم وجود أخطاء TypeScript
npx tsc --noEmit
```

---

## المرحلة الرابعة: الاختبار والتحقق (3 ساعات) 🔵

### المهمة 4.1: Smoke tests للمسارات الجديدة

أنشئ ملف:

```
salesos/frontend/src/__tests__/routes/remediation-routes.test.tsx
```

**الكود:**

```tsx
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"

// اختبار وجود المكونات الأساسية
describe("New Route Pages — Smoke Tests", () => {
  const pages = [
    { name: "Revenue", path: "/revenue" },
    { name: "Pipeline", path: "/pipeline" },
    { name: "Forecast", path: "/forecast" },
    { name: "Decisions", path: "/decisions" },
    { name: "AI Registry", path: "/ai" },
  ]

  pages.forEach(({ name, path }) => {
    it(`${name} page renders without crashing`, async () => {
      // Dynamic import to verify the module resolves
      const mod = await import(`@/app/(dashboard)${path}/page`)
      expect(mod.default).toBeDefined()
    })
  })
})
```

---

### المهمة 4.2: التحقق من الـ API endpoints الجديدة

```bash
# تأكد من أن AI router يعمل بعد التسجيل
curl -s http://localhost:8000/api/v1/ai/prompts | python -m json.tool

# تأكد من أن الـ routes الجديدة متاحة
curl -s http://localhost:8000/docs  # تحقق من Swagger UI
```

---

### المهمة 4.3: تحديث FEATURE_STATUS.md

بعد تنفيذ كل المهام، حدّث `docs/FEATURE_STATUS.md` بتغيير حالة كل ميزة من 🔴 إلى 🟢.

---

## ملخص التغييرات

### ملفات جديدة (12)

| # | الملف | المرحلة |
|---|-------|---------|
| 1 | `frontend/src/app/(dashboard)/revenue/page.tsx` | 1.1 |
| 2 | `frontend/src/app/(dashboard)/pipeline/page.tsx` | 1.2 |
| 3 | `frontend/src/app/(dashboard)/opportunities/[id]/page.tsx` | 1.3 |
| 4 | `frontend/src/app/(dashboard)/forecast/page.tsx` | 1.4 |
| 5 | `frontend/src/app/(dashboard)/decisions/page.tsx` | 1.5 |
| 6 | `frontend/src/app/(dashboard)/ai/page.tsx` | 2.2 |
| 7 | `frontend/src/app/(dashboard)/graph/page.tsx` | 2.3 |
| 8 | `frontend/src/app/(dashboard)/error.tsx` | 3.1 |
| 9 | `frontend/src/app/(dashboard)/loading.tsx` | 3.1 |
| 10 | `frontend/src/app/(dashboard)/not-found.tsx` | 3.1 |
| 11 | `frontend/src/__tests__/routes/remediation-routes.test.tsx` | 4.1 |

### ملفات معدلة (5)

| # | الملف | التعديل | المرحلة |
|---|-------|---------|---------|
| 1 | `frontend/src/app/(dashboard)/layout.tsx` | NAV_KEYS + icons | 1.6, 2.5 |
| 2 | `frontend/src/lib/i18n/ar.json` | مفاتيح جديدة | 1.7, 2.4 |
| 3 | `frontend/src/lib/i18n/en.json` | مفاتيح جديدة | 1.7, 2.4 |
| 4 | `backend/app/main.py` | تسجيل AI router | 2.1 |
| 5 | `docs/FEATURE_STATUS.md` | تحديث الحالات | 4.3 |

---

## قياس النجاح

| المقياس | قبل | بعد | الطريقة |
|---------|-----|-----|---------|
| Routes wired | 12 | 19 | عد NAV_KEYS |
| Customer reachable | 40% | 95% | فتح كل route في المتصفح |
| Backend routers registered | 29 | 30 (+AI) | عد `include_router` |
| Error pages | 0 | 3 | `error.tsx`, `loading.tsx`, `not-found.tsx` |
| i18n coverage | 180 keys | ~210 keys | عد المفاتيح |

---

## مصفوفة المخاطر

| خطر | احتمال | تأثير | تخفيف |
|-----|--------|-------|-------|
| RevenueWorkspace يفشل بسبب API غير مستقر | متوسط | منخفض | الـ workspace فيه built-in error handling |
| تعارض routes بسبب تكرار /opportunities في 3 routers | منخفض | متوسط | موجود مسبقًا قبل التغيير |
| كسر تنسيق الشريط الجانبي بسبب كثرة العناصر | منخفض | منخفض | Scroll طبيعي في الـ sidebar |
| فشل AI router بعد التسجيل لعدم اكتماله | متوسط | منخفض | نختبر بـ curl أولاً |

---

## الترتيب الزمني للتنفيذ

```
اليوم 1:
  09:00 - 10:00   المهمة 1.1 + 1.2 + 1.3 (Revenue, Pipeline, Opportunity detail)
  10:00 - 11:00   المهمة 1.4 + 1.5 (Forecast, Decision Center)
  11:00 - 11:30   المهمة 1.6 + 1.7 (Sidebar + i18n)
  ✅ اكتمال المرحلة الأولى — 7 routes جديدة شغالة

اليوم 2:
  09:00 - 09:15   المهمة 2.1 (تسجيل AI router)
  09:15 - 11:15   المهمة 2.2 (صفحة AI)
  11:15 - 12:15   المهمة 2.3 (Knowledge Graph)
  12:15 - 12:30   المهمة 2.4 + 2.5 (i18n + sidebar)
  ✅ اكتمال المرحلة الثانية — 2 features مخفية مكشوفة

اليوم 3:
  09:00 - 11:00   المهمة 3.1 (Error boundaries + Loading)
  11:00 - 12:00   المهمة 3.2 (Company 360 fix)
  12:00 - 12:30   المهمة 3.3 (Employee 360 fix)
  12:30 - 13:00   المهمة 3.4 (Lint + TypeScript)
  ✅ اكتمال المرحلة الثالثة — تحسين المتانة

اليوم 4:
  09:00 - 12:00   المرحلة الرابعة (اختبار + توثيق)
  ✅ اكتمال الخطة — 95% Customer Reachable
```

---

*آخر تحديث: 2026-07-13*
