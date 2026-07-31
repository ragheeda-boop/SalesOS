"use client";

import { useState, useEffect, useCallback } from "react";
import { cn } from "@salesos/ui";
import { Clock, Bookmark, BookmarkCheck, Play, Trash2 } from "lucide-react";

interface SearchHistoryEntry {
  query: string;
  strategy: string;
  timestamp: number;
  resultCount?: number;
}

interface SavedSearch {
  id: string;
  name: string;
  query: string;
  strategy: string;
  createdAt: number;
}

const HISTORY_KEY = "salesos-search-history";
const SAVED_KEY = "salesos-saved-searches";
const MAX_HISTORY = 10;

function loadHistory(): SearchHistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(entries: SearchHistoryEntry[]) {
  try {
    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify(entries.slice(0, MAX_HISTORY)),
    );
  } catch {}
}

function loadSaved(): SavedSearch[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(SAVED_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSaved(entries: SavedSearch[]) {
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify(entries));
  } catch {}
}

interface SearchHistoryProps {
  onReRun: (query: string, strategy: string) => void;
  currentQuery?: string;
  currentStrategy?: string;
}

export function SearchHistory({
  onReRun,
  currentQuery,
  currentStrategy,
}: SearchHistoryProps) {
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [saved, setSaved] = useState<SavedSearch[]>([]);
  const [activeTab, setActiveTab] = useState<"recent" | "saved">("recent");
  const [saveMode, setSaveMode] = useState(false);
  const [saveName, setSaveName] = useState("");

  useEffect(() => {
    setHistory(loadHistory());
    setSaved(loadSaved());
  }, []);

  const removeHistory = useCallback(
    (index: number) => {
      const updated = history.filter((_, i) => i !== index);
      setHistory(updated);
      saveHistory(updated);
    },
    [history],
  );

  const toggleSave = useCallback(
    (query: string, strategy: string) => {
      const existing = saved.find(
        (s) => s.query === query && s.strategy === strategy,
      );
      if (existing) {
        const updated = saved.filter((s) => s.id !== existing.id);
        setSaved(updated);
        saveSaved(updated);
      } else {
        const newEntry: SavedSearch = {
          id: `saved-${Date.now()}`,
          name: saveName || query,
          query,
          strategy,
          createdAt: Date.now(),
        };
        const updated = [newEntry, ...saved];
        setSaved(updated);
        saveSaved(updated);
        setSaveName("");
        setSaveMode(false);
      }
    },
    [saved, saveName],
  );

  const removeSaved = useCallback(
    (id: string) => {
      const updated = saved.filter((s) => s.id !== id);
      setSaved(updated);
      saveSaved(updated);
    },
    [saved],
  );

  const isSaved = (query: string, strategy: string) =>
    saved.some((s) => s.query === query && s.strategy === strategy);

  const formatTime = (ts: number) => {
    const diff = Date.now() - ts;
    if (diff < 60_000) return "just now";
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    return new Date(ts).toLocaleDateString();
  };

  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">
          Search History
        </h3>
        <div className="flex gap-1 rounded-lg bg-[var(--bg-secondary)] p-0.5">
          <button
            onClick={() => setActiveTab("recent")}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              activeTab === "recent"
                ? "bg-[var(--bg-primary)] text-[var(--muhide-orange)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]",
            )}
          >
            <Clock className="inline h-3 w-3 mr-1" />
            Recent
          </button>
          <button
            onClick={() => setActiveTab("saved")}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              activeTab === "saved"
                ? "bg-[var(--bg-primary)] text-[var(--muhide-orange)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]",
            )}
          >
            <Bookmark className="inline h-3 w-3 mr-1" />
            Saved ({saved.length})
          </button>
        </div>
      </div>

      {activeTab === "recent" && (
        <div className="space-y-1">
          {history.length === 0 ? (
            <p className="py-4 text-center text-xs text-[var(--text-muted)]">
              No recent searches
            </p>
          ) : (
            history.map((entry, i) => (
              <div
                key={`${entry.query}-${entry.timestamp}`}
                className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-[var(--bg-secondary)] group"
              >
                <button
                  onClick={() => onReRun(entry.query, entry.strategy)}
                  className="flex flex-1 items-center gap-2 text-right"
                >
                  <Play className="h-3 w-3 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-sm text-[var(--text-primary)] truncate">
                    {entry.query}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)] whitespace-nowrap">
                    {entry.strategy}
                  </span>
                  {entry.resultCount !== undefined && (
                    <span className="text-[10px] text-[var(--text-muted)]">
                      ({entry.resultCount})
                    </span>
                  )}
                </button>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {formatTime(entry.timestamp)}
                  </span>
                  <button
                    onClick={() => toggleSave(entry.query, entry.strategy)}
                    className="rounded p-0.5 text-[var(--text-muted)] hover:text-[var(--muhide-orange)] opacity-0 group-hover:opacity-100 transition-opacity"
                    title={
                      isSaved(entry.query, entry.strategy) ? "Unsave" : "Save"
                    }
                  >
                    {isSaved(entry.query, entry.strategy) ? (
                      <BookmarkCheck className="h-3 w-3" />
                    ) : (
                      <Bookmark className="h-3 w-3" />
                    )}
                  </button>
                  <button
                    onClick={() => removeHistory(i)}
                    className="rounded p-0.5 text-[var(--text-muted)] hover:text-[var(--status-danger-text)] opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remove"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === "saved" && (
        <div className="space-y-1">
          {saveMode && (
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="Save name (optional)"
                className="flex-1 rounded-md border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-primary)]"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && currentQuery) {
                    toggleSave(currentQuery, currentStrategy || "hybrid");
                  }
                }}
              />
              <button
                onClick={() => {
                  if (currentQuery)
                    toggleSave(currentQuery, currentStrategy || "hybrid");
                }}
                className="rounded-md bg-[var(--muhide-orange)] px-2 py-1 text-xs text-white hover:brightness-90"
              >
                Save
              </button>
              <button
                onClick={() => setSaveMode(false)}
                className="rounded-md px-2 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                Cancel
              </button>
            </div>
          )}

          {!saveMode && currentQuery && (
            <button
              onClick={() => setSaveMode(true)}
              className="mb-2 flex items-center gap-1 rounded-md border border-dashed border-[var(--border-default)] px-2 py-1.5 text-xs text-[var(--text-muted)] hover:border-[var(--muhide-orange)] hover:text-[var(--muhide-orange)] w-full justify-center"
            >
              <Bookmark className="h-3 w-3" />
              Save current search
            </button>
          )}

          {saved.length === 0 ? (
            <p className="py-4 text-center text-xs text-[var(--text-muted)]">
              No saved searches
            </p>
          ) : (
            saved.map((entry) => (
              <div
                key={entry.id}
                className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-[var(--bg-secondary)] group"
              >
                <button
                  onClick={() => onReRun(entry.query, entry.strategy)}
                  className="flex flex-1 items-center gap-2 text-right"
                >
                  <Play className="h-3 w-3 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="flex flex-col">
                    <span className="text-sm text-[var(--text-primary)]">
                      {entry.name}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {entry.query} · {entry.strategy}
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => removeSaved(entry.id)}
                  className="rounded p-0.5 text-[var(--text-muted)] hover:text-[var(--status-danger-text)] opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
