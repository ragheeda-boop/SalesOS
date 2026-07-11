"use client";

import { useState } from "react";
import { useSearch } from "@/lib/hooks/searchQueries";
import { useRouter } from "next/navigation";
import { Search, Loader2, Building2, FileText, Users, Hash, ChevronLeft, ChevronRight, Filter } from "lucide-react";
import { Input } from "@salesos/ui";
import { Badge, cn } from "@salesos/ui";

type Strategy = "fulltext" | "semantic" | "hybrid";

const STRATEGY_LABELS: Record<Strategy, string> = {
  fulltext: "نص كامل",
  semantic: "دلالي",
  hybrid: "مختلط",
};

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("hybrid");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data, isLoading, error } = useSearch(
    searchQuery ? { q: searchQuery, strategy, limit: pageSize, offset: page * pageSize, include_facets: true } : { q: "", strategy }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(query);
    setPage(0);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6" dir="rtl">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">البحث المتقدم</h1>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">ابحث في الشركات والسجلات التجارية</p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-neutral-400" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ابحث باسم الشركة، رقم السجل، النشاط..."
            className="pr-10 text-base"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="rounded-lg bg-[var(--muhide-orange)] px-6 py-2 text-sm font-medium text-white hover:bg-orange-700 disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "بحث"}
        </button>
      </form>

      {/* Strategy toggle */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-neutral-500">استراتيجية البحث:</span>
        <div className="flex gap-1 rounded-lg bg-neutral-100 p-1 dark:bg-neutral-800">
          {(["fulltext", "semantic", "hybrid"] as Strategy[]).map((s) => (
            <button
              key={s}
              onClick={() => { setStrategy(s); setPage(0); }}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                strategy === s
                  ? "bg-white text-[var(--muhide-orange)] shadow-muhide-1 dark:bg-neutral-700 dark:text-orange-300"
                  : "text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200"
              )}
            >
              {STRATEGY_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {error && (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700 dark:border-danger-800 dark:bg-danger-900/20 dark:text-danger-400">
          حدث خطأ أثناء البحث
        </div>
      )}

      {searchQuery && !isLoading && data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              {data.total} نتيجة ({(data.took_ms / 1000).toFixed(2)} ثانية)
              {data.strategy && <> — استراتيجية: {STRATEGY_LABELS[data.strategy as Strategy] || data.strategy}</>}
            </p>
          </div>

          {data.items.length === 0 ? (
            <div className="rounded-lg border border-dashed border-neutral-300 p-12 text-center dark:border-neutral-600">
              <Search className="mx-auto mb-3 h-10 w-10 text-neutral-300 dark:text-neutral-600" />
              <p className="text-neutral-500 dark:text-neutral-400">لا توجد نتائج</p>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {data.items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => router.push(`/companies/${item.id}`)}
                    className="cursor-pointer rounded-lg border border-neutral-200 bg-white p-4 transition-colors hover:border-orange-300 hover:shadow-muhide-1 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-orange-600"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">
                          {String(item.data?.name_ar || item.data?.name_en || "—")}
                        </h3>
                        {!!item.data?.cr_number && (
                          <p className="flex items-center gap-1 text-xs text-neutral-500 dark:text-neutral-400">
                            <Hash className="h-3 w-3" />
                            {String(item.data.cr_number as string)}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-2 text-xs text-neutral-500 dark:text-neutral-400">
                          {!!item.data?.city && <span>{String(item.data.city as string)}</span>}
                          {!!item.data?.industry && <span>{String(item.data.industry as string)}</span>}
                          {!!item.data?.status && (
                            <Badge variant={item.data.status === "active" ? "success" : "default"}>
                              {String((item.data as Record<string, unknown>).status as string)}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-neutral-400 dark:text-neutral-500">
                          {Math.round(item.score * 100)}%
                        </span>
                        <ChevronLeft className="h-4 w-4 text-neutral-300 dark:text-neutral-600" />
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
                    className="rounded-lg border p-2 hover:bg-neutral-50 disabled:opacity-30 dark:border-neutral-700 dark:hover:bg-neutral-800"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    الصفحة {page + 1} من {Math.ceil(data.total / pageSize)}
                  </span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={(page + 1) * pageSize >= data.total}
                    className="rounded-lg border p-2 hover:bg-neutral-50 disabled:opacity-30 dark:border-neutral-700 dark:hover:bg-neutral-800"
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
        <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-700 dark:bg-neutral-800">
          <h3 className="mb-3 text-sm font-semibold text-neutral-900 dark:text-neutral-100">تصفية حسب</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Object.entries(data.facets).map(([field, values]) => (
              <div key={field}>
                <p className="mb-1 text-xs font-medium text-neutral-500 dark:text-neutral-400">{field}</p>
                <div className="space-y-1">
                  {Object.entries(values).slice(0, 5).map(([value, count]) => (
                    <div key={value} className="flex items-center justify-between text-xs text-neutral-700 dark:text-neutral-300">
                      <span>{value}</span>
                      <span className="text-neutral-400">({count})</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
