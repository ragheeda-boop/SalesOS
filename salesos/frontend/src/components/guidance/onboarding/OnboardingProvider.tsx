"use client"

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react"

const ONBOARDING_KEY = "salesos:onboarding-progress"

export interface OnboardingItem {
  id: string
  label: string
  href: string
  tourId?: string
}

const DEFAULT_ITEMS: OnboardingItem[] = [
  { id: "profile", label: "أكمل ملفك الشخصي", href: "/settings", tourId: "welcome" },
  { id: "pipeline", label: "استورد خط الأنابيب", href: "/opportunities", tourId: "pipeline" },
  { id: "workflow", label: "أنشئ أول سير عمل", href: "/automation", tourId: "workflow" },
  { id: "team", label: "ادعُ أعضاء الفريق", href: "/admin" },
  { id: "integrations", label: "اضبط التكاملات", href: "/settings" },
  { id: "nba", label: "شغّل أول تحليل NBA", href: "/dashboard", tourId: "nba" },
]

interface OnboardingContextValue {
  items: OnboardingItem[]
  completed: string[]
  completeItem: (id: string) => void
  isComplete: boolean
  progress: number
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null)

function loadCompleted(): string[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(ONBOARDING_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveCompleted(completed: string[]) {
  try {
    localStorage.setItem(ONBOARDING_KEY, JSON.stringify(completed))
  } catch {
    // localStorage unavailable
  }
}

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [completed, setCompleted] = useState<string[]>(loadCompleted)

  useEffect(() => {
    saveCompleted(completed)
  }, [completed])

  const completeItem = useCallback((id: string) => {
    setCompleted((prev) => {
      if (prev.includes(id)) return prev
      return [...prev, id]
    })
  }, [])

  const isComplete = completed.length >= DEFAULT_ITEMS.length
  const progress = Math.round((completed.length / DEFAULT_ITEMS.length) * 100)

  return (
    <OnboardingContext.Provider
      value={{
        items: DEFAULT_ITEMS,
        completed,
        completeItem,
        isComplete,
        progress,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  )
}

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext)
  if (!ctx) throw new Error("useOnboarding must be used within an OnboardingProvider")
  return ctx
}
