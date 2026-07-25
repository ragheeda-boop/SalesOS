"use client";

import { useState, useCallback, useEffect } from"react";
import { useSearch } from"@/lib/hooks/searchQueries";
import { useRouter } from"next/navigation";
import Link from"next/link";
import { Search, Hash, ChevronLeft, ChevronRight, BarChart3 } from"lucide-react";
import { Input, Spinner } from"@salesos/ui";
import { Badge, cn } from"@salesos/ui";
import { ErrorFallback } from"@/components/foundation/error-boundary";
import { useTranslation } from"@/lib/i18n";
import { SearchHistory } from"@/components/search/SearchHistory";

type Strategy ="fulltext" |"semantic" |"hybrid";

const STRATEGY_KEYS: Record<Strategy, string> = {
 fulltext:"search.fulltext",
 semantic:"search.semantic",
 hybrid:"search.hybrid",
};

export default function SearchPage() {
 const router = useRouter();
 const { t } = useTranslation();
 const [query, setQuery] = useState("");
 const [searchQuery, setSearchQuery] = useState("");
 const [strategy, setStrategy] = useState<Strategy>("hybrid");
 const [page, setPage] = useState(0);
 const pageSize = 20;

 const { data, isLoading, error, refetch } = useSearch(
 searchQuery ? { q: searchQuery, strategy, limit: pageSize, offset: page * pageSize, include_facets: true } : { q:"", strategy }
 );

 const handleSearch = useCallback(
 (e: React.FormEvent) => {
 e.preventDefault();
 setSearchQuery(query);
 setPage(0);
 },
 [query]
 );

 const handleReRun = useCallback(
 (q: string, s: string) => {
 setQuery(q);
 setStrategy(s as Strategy);
 setSearchQuery(q);
 setPage(0);
 },
 []
 );

 // Track search in history when results arrive
 const trackHistory = useCallback(
 (query: string, strategy: string, resultCount: number) => {
 try {
 const raw = localStorage.getItem("salesos-search-history");
 const history = raw ? JSON.parse(raw) : [];
 const entry = { query, strategy, timestamp: Date.now(), resultCount };
 const updated = [entry, ...history.filter((h: { query: string; strategy: string }) => h.query !== query || h.strategy !== strategy)].slice(0, 10);
 localStorage.setItem("salesos-search-history", JSON.stringify(updated));
 } catch {}
 },
 []
 );

 // Auto-track when search results arrive
 useEffect(() => {
 if (searchQuery && data && !isLoading) {
 trackHistory(searchQuery, strategy, data.total);
 }
 }, [searchQuery, data, isLoading, strategy, trackHistory]);

 return (
 <div className="mx-auto max-w-5xl space-y-6">
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("search.title")}</h1>
 <p className="mt-1 text-sm text-[var(--text-muted)]">{t("search.subtitle")}</p>
 </div>
 <Link
 href="/search/analytics"
 className="flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] hover:border-[var(--muhide-orange)] hover:text-[var(--muhide-orange)] transition-colors"
 >
 <BarChart3 className="h-3.5 w-3.5" />
 {t("analytics.search_analytics")}
 </Link>
 </div>

 {/* Search bar */}
 <form onSubmit={handleSearch} className="flex gap-3">
 <div className="relative flex-1">
 <Search className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--text-disabled)]" />
 <Input
 value={query}
 onChange={(e) => setQuery(e.target.value)}
 placeholder={t("search.placeholder")}
 className="pr-10 text-base"
 />
 </div>
 <button
 type="submit"
 disabled={!query.trim() || isLoading}
            className="rounded-lg bg-[var(--muhide-orange)] px-6 py-2 text-sm font-medium text-white hover:brightness-90 disabled:opacity-50"
 >
 {isLoading ? <Spinner className="h-4 w-4" /> : t("search.button")}
 </button>
 </form>

 {/* Strategy toggle */}
 <div className="flex items-center gap-2">
 <span className="text-xs font-medium text-[var(--text-muted)]">{t("search.strategy")}</span>
 <div className="flex gap-1 rounded-lg bg-[var(--bg-tertiary)] p-1">
 {(["fulltext","semantic","hybrid"] as Strategy[]).map((s) => (
 <button
 key={s}
 onClick={() => { setStrategy(s); setPage(0); }}
 className={cn(
"rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
 strategy === s
 ?"bg-[var(--bg-primary)] text-[var(--muhide-orange)] shadow-muhide-1 dark:text-orange-300"
 :"text-[var(--text-secondary)] hover:text-[var(--text-primary)] dark:hover:text-[var(--text-disabled)]"
 )}
 >
 {t(STRATEGY_KEYS[s])}
 </button>
 ))}
 </div>
 </div>

 {/* Results */}
 {error && (
 <ErrorFallback
 title={t("search.error")}
 message={(error as Error)?.message || t("search.error_hint")}
 onRetry={() => refetch()}
 showDetails={process.env.NODE_ENV ==="development"}
 errorDetails={String(error)}
 />
 )}

 {searchQuery && !isLoading && data && (
 <div className="space-y-4">
 <div className="flex items-center justify-between">
 <p className="text-sm text-[var(--text-muted)]">
 {t("search.results_count", { count: data.total, time: (data.took_ms / 1000).toFixed(2) })}
 {data.strategy && <> — {t("search.strategy_label", { strategy: t(STRATEGY_KEYS[data.strategy as Strategy] ||"") })}</>}
 </p>
 </div>

 {data.items.length === 0 ? (
 <div className="rounded-lg border border-dashed border-[var(--border-hover)] p-12 text-center">
 <Search className="mx-auto mb-3 h-10 w-10 text-[var(--text-disabled)]" />
 <p className="text-[var(--text-muted)]">{t("search.no_results")}</p>
 </div>
 ) : (
 <>
 <div className="space-y-3">
 {data.items.map((item) => (
 <div
 key={item.id}
 onClick={() => router.push(`/companies/${item.id}`)}
                  className="cursor-pointer rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 transition-colors hover:border-[var(--border-active)] hover:shadow-muhide-1"
 >
 <div className="flex items-start justify-between">
 <div className="space-y-1">
 <h3 className="font-semibold text-[var(--text-primary)]">
 {String(item.data?.name_ar || item.data?.name_en ||"\u2014")}
 </h3>
 {!!item.data?.cr_number && (
 <p className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
 <Hash className="h-3 w-3" />
 {String(item.data.cr_number as string)}
 </p>
 )}
 <div className="flex flex-wrap gap-2 text-xs text-[var(--text-muted)]">
 {!!item.data?.city && <span>{String(item.data.city as string)}</span>}
 {!!item.data?.industry && <span>{String(item.data.industry as string)}</span>}
 {!!item.data?.status && (
 <Badge variant={item.data.status ==="active" ?"success" :"default"}>
 {String((item.data as Record<string, unknown>).status as string)}
 </Badge>
 )}
 </div>
 </div>
 <div className="flex items-center gap-2">
 <span className="text-xs text-[var(--text-disabled)]">
 {Math.round(item.score * 100)}%
 </span>
 <ChevronLeft className="h-4 w-4 text-[var(--text-disabled)]" />
 </div>
 </div>
 </div>
 ))}
 </div>

 {/* Pagination */}
 {data.total > pageSize && (
 <div className="flex items-center justify-center gap-2">
 <button
 onClick={() => setPage((p) => Math.max(0, p - 1))}
 disabled={page === 0}
 className="rounded-lg border p-2 hover:bg-[var(--bg-secondary)] disabled:opacity-30 dark:hover:bg-[var(--bg-secondary)]"
 aria-label={t("search.prev_page")}
 >
 <ChevronRight className="h-4 w-4" />
 </button>
 <span className="text-sm text-[var(--text-secondary)]">
 {t("search.page_of", { page: page + 1, total: Math.ceil(data.total / pageSize) })}
 </span>
 <button
 onClick={() => setPage((p) => p + 1)}
 disabled={(page + 1) * pageSize >= data.total}
 className="rounded-lg border p-2 hover:bg-[var(--bg-secondary)] disabled:opacity-30 dark:hover:bg-[var(--bg-secondary)]"
 aria-label={t("search.next_page")}
 >
 <ChevronLeft className="h-4 w-4" />
 </button>
 </div>
 )}
 </>
 )}
 </div>
 )}

 {/* Facets sidebar */}
 {data?.facets && Object.keys(data.facets).length > 0 && (
 <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">{t("search.filter_by")}</h3>
 <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
 {Object.entries(data.facets).map(([field, values]) => (
 <div key={field}>
 <p className="mb-1 text-xs font-medium text-[var(--text-muted)]">{field}</p>
 <div className="space-y-1">
 {Object.entries(values).slice(0, 5).map(([value, count]) => (
 <div key={value} className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
 <span>{value}</span>
 <span className="text-[var(--text-disabled)]">({count})</span>
 </div>
 ))}
 </div>
 </div>
 ))}
 </div>
 </div>
 )}

 {/* Search History */}
 <SearchHistory
 onReRun={handleReRun}
 currentQuery={searchQuery}
 currentStrategy={strategy}
 />
 </div>
 );
}
