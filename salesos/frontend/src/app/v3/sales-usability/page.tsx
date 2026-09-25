"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import {
  fetchSalesUsabilityAccounts,
  fetchSalesUsabilitySummary,
} from "@/lib/reviewQueueQueries";

const PAGE_SIZE = 100;

const BLOCKER_LABELS: Record<string, string> = {
  P1_REVIEW_GATE_OPEN: "مراجعة P1 مفتوحة (G4)",
  P2_STRATUM_NOT_ACCEPTED: "شريحة P2 غير مقبولة (G5)",
  PENDING_P3_FUZZY_PAIR: "زوج تشابه P3 معلّق (G2)",
  PENDING_SHORT_CR_ADJUDICATION: "سجل تجاري قصير معلّق (G3)",
  CR_SUSPICIOUS_MULTI: "سجل تجاري متعدد القيم (G3)",
  NON_COMMERCIAL_SEGMENT: "جهة غير تجارية (جمعية/حكومية)",
  OUT_OF_MARKET: "خارج السوق المستهدف",
  PLACEHOLDER_ACCOUNT_NAME: "اسم حساب وهمي (خطأ ترحيل بيانات)",
};

type UsableFilter = "all" | "usable" | "blocked";

function blockerLabel(code: string) {
  return BLOCKER_LABELS[code] ?? code;
}

export default function SalesUsabilityPage() {
  const { ready, hasToken } = useAccessToken();
  const [usable, setUsable] = useState<UsableFilter>("all");
  const [blocker, setBlocker] = useState("");
  const [page, setPage] = useState(1);

  const summary = useQuery({
    queryKey: ["sales-usability", "summary"],
    queryFn: fetchSalesUsabilitySummary,
    enabled: ready && hasToken,
  });
  const accounts = useQuery({
    queryKey: ["sales-usability", "accounts", usable, blocker, page],
    queryFn: () =>
      fetchSalesUsabilityAccounts({
        usable: usable === "all" ? undefined : usable === "usable",
        blocker,
        page,
        pageSize: PAGE_SIZE,
      }),
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/sales-usability" />;

  const s = summary.data;
  const items = accounts.data?.items ?? [];
  const total = accounts.data?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="p-6">
      <PageHeader
        title="Sales Usability"
        description="أي الحسابات الجاهزة للبيع يمكن استخدامها فعلًا، ولماذا لا يمكن استخدام البقية."
        actions={
          <Link
            href="/v3/review-queue"
            className="rounded border border-border px-3 py-2 text-sm hover:bg-secondary"
          >
            طابور المراجعة
          </Link>
        }
      />

      <div className="mb-5 rounded-lg border border-[var(--status-warning-border)] bg-[var(--status-warning-bg)] p-4 text-sm text-[var(--status-warning-text)]">
        عرض للقراءة فقط. لا تفتح هذه الشاشة أي بوابة ولا تعتمد أي حساب؛ البوابات تُغلق بقرار بشري موثّق.
      </div>

      {summary.isLoading ? (
        <LoadingState />
      ) : summary.isError ? (
        <ErrorState description="تعذّر تحميل الملخص." onRetry={() => summary.refetch()} />
      ) : s ? (
        <section aria-label="Summary" className="mb-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-border p-4">
            <div className="text-sm text-muted-foreground">حسابات جاهزة للبيع</div>
            <div className="text-2xl font-semibold" data-testid="ready-count">
              {s.ready_accounts.toLocaleString("en-US")}
            </div>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="text-sm text-muted-foreground">قابلة للاستخدام الآن</div>
            <div className="text-2xl font-semibold" data-testid="usable-count">
              {s.usable_accounts.toLocaleString("en-US")}
            </div>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="mb-2 text-sm text-muted-foreground">البوابات</div>
            <ul className="space-y-1 text-sm">
              {Object.entries(s.gates).map(([key, g]) => (
                <li key={key} title={g.source}>
                  <span className="font-mono">{key}</span>: {g.status}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border border-border p-4 md:col-span-3">
            <div className="mb-2 text-sm text-muted-foreground">أسباب الحجب</div>
            <ul className="grid gap-1 text-sm md:grid-cols-2">
              {Object.entries(s.by_blocker).map(([code, n]) => (
                <li key={code}>
                  {blockerLabel(code)}: <strong>{n.toLocaleString("en-US")}</strong>
                </li>
              ))}
            </ul>
          </div>
        </section>
      ) : null}

      <section aria-label="Accounts" className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            الحالة
            <select
              value={usable}
              onChange={(e) => {
                setUsable(e.target.value as UsableFilter);
                setPage(1);
              }}
              className="rounded border bg-background px-3 py-2"
            >
              <option value="all">الكل</option>
              <option value="usable">قابل للاستخدام</option>
              <option value="blocked">محجوب</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            سبب الحجب
            <select
              value={blocker}
              onChange={(e) => {
                setBlocker(e.target.value);
                setPage(1);
              }}
              className="rounded border bg-background px-3 py-2"
            >
              <option value="">الكل</option>
              {Object.keys(BLOCKER_LABELS).map((code) => (
                <option key={code} value={code}>
                  {BLOCKER_LABELS[code]}
                </option>
              ))}
            </select>
          </label>
          <span className="text-sm text-muted-foreground">{total.toLocaleString("en-US")} حساب</span>
        </div>

        {accounts.isLoading ? (
          <LoadingState />
        ) : accounts.isError ? (
          <ErrorState description="تعذّر تحميل الحسابات." onRetry={() => accounts.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState title="لا توجد حسابات مطابقة" />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-secondary text-left">
                <tr>
                  <th className="px-3 py-2">الشركة</th>
                  <th className="px-3 py-2">النطاق</th>
                  <th className="px-3 py-2">المدينة</th>
                  <th className="px-3 py-2">الجاهزية</th>
                  <th className="px-3 py-2">الأولوية</th>
                  <th className="px-3 py-2">أسباب الحجب</th>
                </tr>
              </thead>
              <tbody>
                {items.map((a) => (
                  <tr key={a.global_company_id} className="border-t border-border">
                    <td className="px-3 py-2">{a.name ?? a.slug ?? a.global_company_id}</td>
                    <td className="px-3 py-2">{a.domain ?? "—"}</td>
                    <td className="px-3 py-2">{a.city ?? "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs">{a.sales_readiness}</td>
                    <td className="px-3 py-2">{a.review_priority ?? "—"}</td>
                    <td className="px-3 py-2">
                      {a.usable ? "قابل للاستخدام" : a.blockers.map(blockerLabel).join("، ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center gap-3 text-sm">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border border-border px-3 py-1 disabled:opacity-50"
          >
            السابق
          </button>
          <span>
            {page} / {lastPage}
          </span>
          <button
            type="button"
            disabled={page >= lastPage}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border border-border px-3 py-1 disabled:opacity-50"
          >
            التالي
          </button>
        </div>
      </section>
    </main>
  );
}
