"use client";

import { useEffect, useState } from "react";
import { Moon, Search, Sparkles, Sun } from "lucide-react";
import { cn } from "@salesos/ui";

type V3TopbarProps = {
  onOpenCommand: () => void;
  onOpenAi: () => void;
  className?: string;
};

function isMacPlatform(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent);
}

function readIsDark(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.classList.contains("dark");
}

export function V3Topbar({ onOpenCommand, onOpenAi, className }: V3TopbarProps) {
  const [isDark, setIsDark] = useState(false);
  const [modKey, setModKey] = useState("Ctrl");

  useEffect(() => {
    setIsDark(readIsDark());
    setModKey(isMacPlatform() ? "⌘" : "Ctrl");
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    const next = root.classList.contains("dark") ? "light" : "dark";
    root.classList.remove("light", "dark");
    root.classList.add(next);
    try {
      localStorage.setItem("salesos_theme", next);
    } catch {
      /* ignore */
    }
    setIsDark(next === "dark");
  };

  return (
    <header
      className={cn(
        "flex h-12 shrink-0 items-center justify-between gap-3 border-b border-[var(--border-default)] bg-[var(--bg-primary)] px-4",
        className
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        <span
          className="truncate text-sm font-medium text-[var(--text-primary)]"
          style={{ fontFamily: "var(--font-ui)" }}
        >
          Workspace
        </span>
        <span className="hidden text-[11px] text-[var(--text-muted)] sm:inline">
          SalesOS · Design Program
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenCommand}
          className="hidden h-8 max-w-[220px] items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2.5 text-left text-[13px] text-[var(--text-muted)] transition-colors hover:border-[var(--border-hover)] hover:text-[var(--text-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] sm:inline-flex"
          aria-label="Open command palette"
        >
          <Search className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="flex-1 truncate">Search or go to…</span>
          <kbd className="rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--text-muted)]">
            {modKey}K
          </kbd>
        </button>

        <button
          type="button"
          onClick={onOpenCommand}
          className="inline-flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] sm:hidden"
          aria-label="Open command palette"
        >
          <Search className="h-4 w-4" aria-hidden />
        </button>

        <button
          type="button"
          onClick={onOpenAi}
          className="inline-flex h-8 items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--border-default)] px-2.5 text-[12px] font-medium text-[var(--text-secondary)] transition-colors hover:border-[var(--border-hover)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          aria-haspopup="dialog"
          aria-label="Open Ask AI popup"
          title="Ask AI opens as a popup (Ctrl+Shift+A) — not part of page layout"
        >
          <Sparkles className="h-3.5 w-3.5 text-[var(--muhide-orange)]" aria-hidden />
          <span className="hidden sm:inline">Ask AI</span>
        </button>

        <button
          type="button"
          onClick={toggleTheme}
          className="inline-flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
        >
          {isDark ? (
            <Sun className="h-4 w-4" aria-hidden />
          ) : (
            <Moon className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>
    </header>
  );
}
