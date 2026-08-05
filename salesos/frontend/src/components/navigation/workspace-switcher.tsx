"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@salesos/ui";
import { ChevronDown } from "lucide-react";
import { workspaces, type Workspace } from "@/lib/workspaces";
import { useTranslation } from "@/lib/i18n";

interface WorkspaceSwitcherProps {
  current: Workspace;
  onSelect: (ws: Workspace) => void;
  collapsed?: boolean;
}

export function WorkspaceSwitcher({
  current,
  onSelect,
  collapsed = false,
}: WorkspaceSwitcherProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const { t } = useTranslation();
  const Icon = current.icon;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    },
    [],
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (collapsed) {
    return (
      <div className="relative" ref={ref} onKeyDown={handleKeyDown}>
        <button
          ref={triggerRef}
          onClick={() => setOpen(!open)}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
          aria-label={t("workspace.switcher")}
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          <Icon className="h-5 w-5" />
        </button>
        {open && (
          <div
            role="listbox"
            aria-label={t("workspace.switcher")}
            className="absolute start-full top-0 z-50 ms-2 min-w-[180px] rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-4 py-1"
          >
            {workspaces.map((ws) => {
              const WsIcon = ws.icon;
              return (
                <button
                  key={ws.id}
                  role="option"
                  aria-selected={ws.id === current.id}
                  onClick={() => {
                    onSelect(ws);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex items-center gap-2 w-full px-3 py-2 text-sm transition",
                    ws.id === current.id
                      ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]",
                  )}
                >
                  <WsIcon className="h-4 w-4 shrink-0" />
                  <span>{t(ws.key)}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative" ref={ref} onKeyDown={handleKeyDown}>
      <button
        ref={triggerRef}
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-[var(--bg-tertiary)] transition"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
          <Icon className="h-4 w-4" />
        </span>
        <span className="flex-1 text-start font-medium text-[var(--text-primary)]">
          {t(current.key)}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-[var(--text-muted)] transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open && (
        <div
          role="listbox"
          aria-label={t("workspace.switcher")}
          className="absolute start-0 top-full z-50 mt-1 w-full min-w-[200px] rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-4 py-1"
        >
          {workspaces.map((ws) => {
            const WsIcon = ws.icon;
            return (
              <button
                key={ws.id}
                role="option"
                aria-selected={ws.id === current.id}
                onClick={() => {
                  onSelect(ws);
                  setOpen(false);
                }}
                className={cn(
                  "flex items-center gap-2 w-full px-3 py-2 text-sm transition",
                  ws.id === current.id
                    ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]",
                )}
              >
                <WsIcon className="h-4 w-4 shrink-0" />
                <span>{t(ws.key)}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
