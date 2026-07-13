"use client"

import { useState } from "react"
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
