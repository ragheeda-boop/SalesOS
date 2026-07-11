"use client"

import { createContext, useContext, useState, useCallback, useRef, useEffect, type ReactNode } from "react"

interface Hint {
  hintId: string
  target: string
  message: string
  tourId?: string
}

interface CoachMarkContextValue {
  hints: Hint[]
  showHint: (hintId: string, target: string, message: string, tourId?: string) => void
  dismissHint: (hintId: string) => void
}

const CoachMarkContext = createContext<CoachMarkContextValue | null>(null)

export function CoachMarkProvider({ children }: { children: ReactNode }) {
  const [hints, setHints] = useState<Hint[]>([])
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  const dismissHint = useCallback((hintId: string) => {
    setHints((prev) => prev.filter((h) => h.hintId !== hintId))
    const timer = timersRef.current.get(hintId)
    if (timer) {
      clearTimeout(timer)
      timersRef.current.delete(hintId)
    }
  }, [])

  const showHint = useCallback(
    (hintId: string, target: string, message: string, tourId?: string) => {
      if (message.length > 100) {
        if (process.env.NODE_ENV === "development") {
          console.warn(`[CoachMark] Message truncated to 100 chars for hint "${hintId}"`)
        }
        message = message.slice(0, 100)
      }

      setHints((prev) => {
        const exists = prev.find((h) => h.hintId === hintId)
        if (exists) return prev
        return [...prev, { hintId, target, message, tourId }]
      })

      const existing = timersRef.current.get(hintId)
      if (existing) clearTimeout(existing)

      const timer = setTimeout(() => {
        dismissHint(hintId)
      }, 5000)
      timersRef.current.set(hintId, timer)
    },
    [dismissHint],
  )

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer))
      timersRef.current.clear()
    }
  }, [])

  return (
    <CoachMarkContext.Provider value={{ hints, showHint, dismissHint }}>
      {children}
    </CoachMarkContext.Provider>
  )
}

export function useCoachMark(): CoachMarkContextValue {
  const ctx = useContext(CoachMarkContext)
  if (!ctx) throw new Error("useCoachMark must be used within a CoachMarkProvider")
  return ctx
}
