"use client"

import { useState } from "react"
import api from "@/lib/api"

export function DemoResetButton() {
  const [resetting, setResetting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleReset = async () => {
    if (!confirm("Reset all demo data? This will re-seed the environment with fresh data.")) return

    setResetting(true)
    setMessage(null)
    setError(null)

    try {
      const res = await api.post("/api/v1/demo/reset")
      const data = res.data
      setMessage(
        `Demo reset complete: ${data.companies} companies, ${data.opportunities} opportunities, ${data.meetings} meetings`
      )
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Reset failed"
      setError(message)
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleReset}
        disabled={resetting}
        className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
      >
        {resetting ? "Resetting..." : "Reset Demo Data"}
      </button>

      {message && <p className="text-sm text-green-600">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
