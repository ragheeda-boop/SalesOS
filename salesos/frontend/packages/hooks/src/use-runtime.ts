import { createContext, useContext } from 'react'
import type { FrontendRuntime } from '@salesos/runtime'

export const RuntimeContext = createContext<FrontendRuntime | null>(null)

export function useRuntime(): FrontendRuntime {
  const runtime = useContext(RuntimeContext)
  if (!runtime) {
    throw new Error('useRuntime must be used within a RuntimeProvider')
  }
  return runtime
}
