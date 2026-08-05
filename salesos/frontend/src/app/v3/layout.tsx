"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { V3Shell } from "@/components/v3/V3Shell";
import { V3Topbar } from "@/components/v3/V3Topbar";
import { V3CommandPalette } from "@/components/v3/V3CommandPalette";
import {
  V3AiPopup,
  V3_AI_OPEN_EVENT,
  type V3AiOpenDetail,
} from "@/components/v3/V3AiPopup";
import { ErrorBoundary } from "@/components/error-boundary";

const SIDEBAR_KEY = "salesos_v3_sidebar_collapsed";

/**
 * SalesOS v3 workspace shell at /v3.
 * AI is popup-only — never a permanent layout region.
 * Not Production GO.
 */
export default function V3Layout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [aiContext, setAiContext] = useState<string | undefined>();

  useEffect(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_KEY);
      if (stored === "1") setCollapsed(true);
    } catch {
      /* ignore */
    }
  }, []);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const openAi = useCallback((contextLabel?: string) => {
    setAiContext(contextLabel);
    setAiOpen(true);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen((open) => !open);
      }
      if (
        (e.metaKey || e.ctrlKey) &&
        e.shiftKey &&
        e.key.toLowerCase() === "a"
      ) {
        e.preventDefault();
        openAi();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [openAi]);

  useEffect(() => {
    const onOpenAi = (e: Event) => {
      const detail = (e as CustomEvent<V3AiOpenDetail>).detail;
      openAi(detail?.contextLabel);
    };
    window.addEventListener(V3_AI_OPEN_EVENT, onOpenAi);
    return () => window.removeEventListener(V3_AI_OPEN_EVENT, onOpenAi);
  }, [openAi]);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <a
        href="#v3-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[var(--z-modal)] focus:rounded-[var(--radius-md)] focus:bg-[var(--bg-primary)] focus:px-3 focus:py-2 focus:text-sm focus:shadow-[var(--shadow-card)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)]"
      >
        Skip to content
      </a>

      <div className="flex min-h-screen">
        <V3Shell collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />

        <div className="flex min-w-0 flex-1 flex-col">
          <V3Topbar
            onOpenCommand={() => setCommandOpen(true)}
            onOpenAi={() => openAi()}
          />
          <main
            id="v3-main"
            className="flex-1 overflow-auto p-5 md:p-6"
            tabIndex={-1}
          >
            <ErrorBoundary>{children}</ErrorBoundary>
          </main>
        </div>
      </div>

      <V3CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
      />
      <V3AiPopup
        open={aiOpen}
        onClose={() => setAiOpen(false)}
        contextLabel={aiContext}
      />
    </div>
  );
}
