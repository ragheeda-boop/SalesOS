"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect, useMemo, type ReactNode } from "react";
import { createFrontendRuntime, type FrontendRuntime } from "@salesos/runtime";
import { RuntimeContext } from "@salesos/hooks";
import { ToastProvider, ToastViewport } from "@salesos/ui";
import { I18nProvider } from "@/lib/i18n";
import { AuthSessionSync } from "@/components/foundation/AuthSessionSync";
import { EntitlementDenialListener } from "@/components/foundation/EntitlementDenialListener";

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
      }),
  );

  const locale = (() => {
    if (typeof window === "undefined") return "ar";
    const stored = localStorage.getItem("salesos-locale");
    if (stored === "en" || stored === "ar") return stored;
    if (navigator.language?.startsWith("ar")) return "ar";
    return "en";
  })();

  const runtime = useMemo<FrontendRuntime>(
    () =>
      createFrontendRuntime({
        wsUrl: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws",
        locale,
        stateOptions: { name: "salesos", debug: false },
      }),
    [locale],
  );

  const [ready, setReady] = useState(false);

  useEffect(() => {
    runtime.localization.setLocale(locale);
    setReady(true);
    return () => runtime.destroy();
  }, [runtime, locale]);

  if (!ready) return null;

  return (
    <ToastProvider>
      <ToastViewport>
        <I18nProvider>
          <RuntimeContext.Provider value={runtime}>
            <QueryClientProvider client={queryClient}>
              <AuthSessionSync />
              <EntitlementDenialListener />
              {children}
            </QueryClientProvider>
          </RuntimeContext.Provider>
        </I18nProvider>
      </ToastViewport>
    </ToastProvider>
  );
}
