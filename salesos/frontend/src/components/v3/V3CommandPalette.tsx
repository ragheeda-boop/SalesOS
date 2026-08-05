"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { cn } from "@salesos/ui";
import { useFocusTrap } from "@/lib/hooks/useFocusTrap";
import { V3_CMD_EXTRA, V3_DOMAIN_NAV, type V3NavItem } from "./nav";

type V3CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
};

function matchesQuery(item: V3NavItem, query: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const hay = [item.label, item.href, ...(item.keywords ?? [])].join(" ").toLowerCase();
  return hay.includes(q);
}

export function V3CommandPalette({ open, onClose }: V3CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const trapRef = useFocusTrap<HTMLDivElement>(open);

  const items = useMemo(() => {
    const all = [...V3_DOMAIN_NAV, ...V3_CMD_EXTRA];
    const seen = new Set<string>();
    return all.filter((item) => {
      if (seen.has(item.href)) return false;
      seen.add(item.href);
      return matchesQuery(item, query);
    });
  }, [query]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [open]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const goTo = useCallback(
    (href: string) => {
      onClose();
      router.push(href);
    },
    [onClose, router]
  );

  const handleKeyDown = useCallback(
    (e: ReactKeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, Math.max(items.length - 1, 0)));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && items[selectedIndex]) {
        e.preventDefault();
        goTo(items[selectedIndex].href);
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [items, selectedIndex, goTo, onClose]
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[var(--z-modal)] flex items-start justify-center pt-[12vh] px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      onClick={onClose}
    >
      <div className="fixed inset-0 bg-[var(--muhide-ink)]/40 backdrop-blur-[2px]" aria-hidden />
      <div
        ref={trapRef}
        className="relative w-full max-w-lg overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-[var(--shadow-card)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 border-b border-[var(--border-default)] px-3">
          <Search className="h-4 w-4 shrink-0 text-[var(--text-muted)]" aria-hidden />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Go to…"
            className="h-11 w-full bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
            aria-autocomplete="list"
            aria-controls="v3-cmd-list"
            autoComplete="off"
            spellCheck={false}
          />
          <kbd className="hidden rounded border border-[var(--border-default)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--text-muted)] sm:inline">
            Esc
          </kbd>
        </div>

        <ul
          id="v3-cmd-list"
          role="listbox"
          aria-label="Go to routes"
          className="max-h-72 overflow-y-auto p-1.5"
        >
          {items.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-[var(--text-muted)]">No matches</li>
          )}
          {items.map((item, index) => {
            const Icon = item.icon;
            const selected = index === selectedIndex;
            return (
              <li key={item.href} role="option" aria-selected={selected}>
                <button
                  type="button"
                  onClick={() => goTo(item.href)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-[var(--radius-md)] px-2.5 py-2 text-left text-[13px] transition-colors",
                    selected
                      ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0 text-[var(--text-muted)]" aria-hidden />
                  <span className="flex-1 truncate font-medium">{item.label}</span>
                  <span className="truncate font-mono text-[11px] text-[var(--text-muted)]">
                    {item.href}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>

        <div className="flex items-center justify-between border-t border-[var(--border-default)] px-3 py-2 text-[11px] text-[var(--text-muted)]">
          <span>Go to</span>
          <span className="flex items-center gap-2">
            <span>↑↓</span>
            <span>↵ open</span>
          </span>
        </div>
      </div>
    </div>
  );
}
