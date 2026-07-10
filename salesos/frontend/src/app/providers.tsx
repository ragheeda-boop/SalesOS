"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState, useEffect, useMemo, type ReactNode } from "react"
import { createFrontendRuntime, type FrontendRuntime } from "@salesos/runtime"
import { RuntimeContext } from "@salesos/hooks"
import { ToastViewport } from "@salesos/ui"

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  const runtime = useMemo<FrontendRuntime>(
    () =>
      createFrontendRuntime({
        wsUrl: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws",
        locale: "ar",
        stateOptions: { name: "salesos", debug: false },
      }),
    []
  )

  const [ready, setReady] = useState(false)

  useEffect(() => {
    runtime.localization.setLocale("ar")
    setReady(true)
    return () => runtime.destroy()
  }, [runtime])

  if (!ready) return null

  return (
    <ToastViewport>
      <RuntimeContext.Provider value={runtime}>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </RuntimeContext.Provider>
    </ToastViewport>
  )
}
