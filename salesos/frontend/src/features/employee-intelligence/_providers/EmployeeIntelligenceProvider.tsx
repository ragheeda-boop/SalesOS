'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useMy360 } from '@/lib/hooks/employeeQueries'
import type { Employee360Response } from '@/lib/api'

interface EmployeeIntelligenceContextValue {
  data: Employee360Response | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}

const EmployeeIntelligenceCtx = createContext<EmployeeIntelligenceContextValue | null>(null)

export function EmployeeIntelligenceProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, isError, error, refetch } = useMy360()

  const value = useMemo<EmployeeIntelligenceContextValue>(
    () => ({ data: data ?? null, isLoading, isError, error, refetch }),
    [data, isLoading, isError, error, refetch],
  )

  return (
    <EmployeeIntelligenceCtx.Provider value={value}>
      {children}
    </EmployeeIntelligenceCtx.Provider>
  )
}

export function useEmployeeIntelligence(): EmployeeIntelligenceContextValue {
  const ctx = useContext(EmployeeIntelligenceCtx)
  if (!ctx) {
    throw new Error('useEmployeeIntelligence must be used within an EmployeeIntelligenceProvider')
  }
  return ctx
}
