"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { cn } from "@salesos/ui";
import { SearchProvider, useSearchContext } from "@salesos/search";
import type { SearchResult } from "@salesos/search";
import {
  SearchInput,
  SearchResultCard,
  SearchSection,
  SearchLoading,
  SearchEmpty,
  SearchHistory,
} from "../components";
import { searchApi } from "@/application/search/search.api";

interface QuickOverlayProps {
  open: boolean;
  onClose: () => void;
  onResultSelect?: (result: SearchResult) => void;
}

function QuickOverlayInner({ open, onClose, onResultSelect }: QuickOverlayProps) {
  const { query, results, total, isLoading, history, search, setQuery } = useSearchContext();
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [query.text]);

  const handleChange = useCallback(
    (value: string) => {
      setQuery({ text: value });
    },
    [setQuery]
  );

  const handleSearch = useCallback(
    (value: string) => {
      if (value.trim().length >= 2) search(value);
    },
    [search]
  );

  const handleClickOverlay = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === overlayRef.current) onClose();
    },
    [onClose]
  );

  if (!open) return null;

  const hasInput = query.text.trim().length >= 2;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-40 flex items-start justify-center bg-black/20 pt-[10vh] backdrop-blur-sm"
      onClick={handleClickOverlay}
    >
      <div
        className={cn(
          "w-full max-w-xl overflow-hidden rounded-2xl border border-[var(--border-color)] bg-[var(--bg-primary)] shadow-xl",
          ""
        )}
      >
        <div className="px-4 py-3">
          <SearchInput
            value={query.text}
            onChange={handleChange}
            onSearch={handleSearch}
            placeholder="ابحث…"
            autoFocus
          />
        </div>

        <div className="max-h-96 overflow-y-auto">
          {/* History when idle */}
          {!hasInput && history.length > 0 && (
            <SearchHistory
              entries={history.slice(0, 5)}
              onClick={(entry) => {
                setQuery({ text: entry.text });
                search(entry.text);
              }}
            />
          )}

          {/* Loading */}
          {isLoading && <SearchLoading count={3} />}

          {/* Results */}
          {hasInput && results.length > 0 && (
            <SearchSection title="النتائج" count={total}>
              {results.slice(0, 8).map((r, i) => (
                <SearchResultCard
                  key={r.id}
                  result={r}
                  highlighted={highlightedIndex === i}
                  onClick={(res) => {
                    onResultSelect?.(res);
                    onClose();
                  }}
                />
              ))}
            </SearchSection>
          )}

          {/* Empty */}
          {hasInput && results.length === 0 && !isLoading && <SearchEmpty query={query.text} />}
        </div>
      </div>
    </div>
  );
}

export function QuickOverlay(props: QuickOverlayProps) {
  return (
    <SearchProvider onSearch={(q) => searchApi(q)}>
      <QuickOverlayInner {...props} />
    </SearchProvider>
  );
}
