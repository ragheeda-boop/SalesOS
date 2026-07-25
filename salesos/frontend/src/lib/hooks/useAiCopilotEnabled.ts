"use client"

import { useEffect, useState } from"react"
import api from"@/lib/api"

/**
 * GA honesty: default False until Settings.feature_ai_copilot is evidence-validated.
 * Lab override: NEXT_PUBLIC_FEATURE_AI_COPILOT=true (still not a GA claim).
 * See docs/audit/ga-engineering-audit/AI_HONESTY.md
 */
export function useAiCopilotEnabled(): { enabled: boolean; ready: boolean } {
 const envOverride = process.env.NEXT_PUBLIC_FEATURE_AI_COPILOT ==="true"
 const [enabled, setEnabled] = useState(envOverride)
 const [ready, setReady] = useState(envOverride)

 useEffect(() => {
 if (envOverride) {
 setEnabled(true)
 setReady(true)
 return
 }
 let cancelled = false
 api
 .get("/api/v1/copilot/status")
 .then((res) => {
 if (cancelled) return
 setEnabled(res.data?.feature_ai_copilot === true)
 setReady(true)
 })
 .catch(() => {
 if (cancelled) return
 setEnabled(false)
 setReady(true)
 })
 return () => {
 cancelled = true
 }
 }, [envOverride])

 return { enabled, ready }
}
