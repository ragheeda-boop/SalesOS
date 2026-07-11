"use client"

import { createContext, useContext, useState, useCallback, useEffect, useRef, type ReactNode } from "react"
import type { TourStep } from "./TourStep"

const COMPLETED_TOURS_KEY = "salesos:completed-tours"

interface TourState {
  tourId: string | null
  currentStep: number
  steps: TourStep[]
  isActive: boolean
}

interface TourContextValue {
  isActive: boolean
  currentStep: number
  steps: TourStep[]
  tourProgress: number
  startTour: (tourId: string, steps: TourStep[]) => void
  nextStep: () => void
  prevStep: () => void
  endTour: () => void
  goToStep: (index: number) => void
  shouldShowTour: (tourId: string) => boolean
  markTourCompleted: (tourId: string) => void
}

const TourContext = createContext<TourContextValue | null>(null)

function getCompletedTours(): string[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(COMPLETED_TOURS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveCompletedTour(tourId: string) {
  try {
    const completed = getCompletedTours()
    if (!completed.includes(tourId)) {
      completed.push(tourId)
      localStorage.setItem(COMPLETED_TOURS_KEY, JSON.stringify(completed))
    }
  } catch {
    // localStorage unavailable
  }
}

export function TourProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<TourState>({
    tourId: null,
    currentStep: 0,
    steps: [],
    isActive: false,
  })

  const beforeCleanupRef = useRef<(() => void) | null>(null)

  const startTour = useCallback((tourId: string, steps: TourStep[]) => {
    setState({
      tourId,
      currentStep: 0,
      steps,
      isActive: true,
    })
  }, [])

  const endTour = useCallback(() => {
    if (beforeCleanupRef.current) {
      beforeCleanupRef.current()
      beforeCleanupRef.current = null
    }
    setState((prev) => {
      if (prev.tourId) saveCompletedTour(prev.tourId)
      return { tourId: null, currentStep: 0, steps: [], isActive: false }
    })
  }, [])

  const runStepAfter = useCallback((step: TourStep) => {
    step.afterStep?.()
  }, [])

  const nextStep = useCallback(() => {
    setState((prev) => {
      if (prev.currentStep >= prev.steps.length - 1) {
        if (prev.tourId) saveCompletedTour(prev.tourId)
        runStepAfter(prev.steps[prev.currentStep])
        return { tourId: null, currentStep: 0, steps: [], isActive: false }
      }
      runStepAfter(prev.steps[prev.currentStep])
      const nextIndex = prev.currentStep + 1
      prev.steps[nextIndex]?.beforeStep?.()
      return { ...prev, currentStep: nextIndex }
    })
  }, [runStepAfter])

  const prevStep = useCallback(() => {
    setState((prev) => {
      if (prev.currentStep <= 0) return prev
      const prevIndex = prev.currentStep - 1
      return { ...prev, currentStep: prevIndex }
    })
  }, [])

  const goToStep = useCallback((index: number) => {
    setState((prev) => {
      if (index < 0 || index >= prev.steps.length) return prev
      return { ...prev, currentStep: index }
    })
  }, [])

  const shouldShowTour = useCallback((tourId: string): boolean => {
    return !getCompletedTours().includes(tourId)
  }, [])

  const markTourCompleted = useCallback((tourId: string) => {
    saveCompletedTour(tourId)
  }, [])

  useEffect(() => {
    if (state.isActive && state.steps[state.currentStep]?.beforeStep) {
      const cleanup = state.steps[state.currentStep].beforeStep!()
      if (typeof cleanup === "function") {
        beforeCleanupRef.current = cleanup
      }
    }
  }, [state.isActive, state.currentStep, state.steps])

  const tourProgress = state.steps.length > 0
    ? Math.round(((state.currentStep + 1) / state.steps.length) * 100)
    : 0

  return (
    <TourContext.Provider
      value={{
        isActive: state.isActive,
        currentStep: state.currentStep,
        steps: state.steps,
        tourProgress,
        startTour,
        nextStep,
        prevStep,
        endTour,
        goToStep,
        shouldShowTour,
        markTourCompleted,
      }}
    >
      {children}
    </TourContext.Provider>
  )
}

export function useTour(): TourContextValue {
  const ctx = useContext(TourContext)
  if (!ctx) throw new Error("useTour must be used within a TourProvider")
  return ctx
}
