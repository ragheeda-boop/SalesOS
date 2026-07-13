"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"
import { Plus, Play, RefreshCw } from "lucide-react"

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
