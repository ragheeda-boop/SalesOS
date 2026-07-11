'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import type { WorkspaceContextValue } from './types'

export function createWorkspaceProvider<W extends Record<string, unknown>, P extends Record<string, unknown> = Record<string, never>>(
  useData: (props: P) => { data: unknown; isLoading: boolean; isError: boolean; error: Error | null; refetch: () => void },
  deriveWidgets: (data: unknown, isLoading: boolean, isError: boolean) => W,
) {
  const WorkspaceContext = createContext<WorkspaceContextValue<W> | null>(null)

  function WorkspaceProvider({ children, onReady, ...props }: { children: ReactNode; onReady?: () => void } & P) {
    const { data, isLoading, isError, error, refetch } = useData(props as unknown as P)
    const widgets = useMemo(() => deriveWidgets(data, isLoading, isError), [data, isLoading, isError])

    useMemo(() => {
      if (!isLoading && widgets) onReady?.()
    }, [isLoading, widgets])

    const value = useMemo<WorkspaceContextValue<W>>(
      () => ({ widgets: widgets as W, isLoading, isError, error, refetch }),
      [widgets, isLoading, isError, error, refetch],
    )

    return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
  }

  function useWorkspaceContext(): WorkspaceContextValue<W> {
    const ctx = useContext(WorkspaceContext)
    if (!ctx) throw new Error('useWorkspaceContext must be used within a WorkspaceProvider')
    return ctx
  }

  return { WorkspaceProvider, useWorkspaceContext }
}
