"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import {
  fetchP3Pairs,
  fetchP3Count,
  fetchShortCR,
  fetchTriage,
  fetchTriageCounts,
  recordDisposition,
} from "@/lib/reviewQueueQueries";

type TabKey = "p3" | "short-cr" | "triage";

const TABS: { key: TabKey; label: string; description: string }[] = [
  { key: "p3", label: "P3 Fuzzy Pairs", description: "114 domain-equal first, then remaining pending" },
  { key: "short-cr", label: "Suspicious Short-CR", description: "36 separator-list CR accounts" },
  { key: "triage", label: "P1/P2 Triage", description: "Read-only review candidate triage" },
];

const P3_DISPOSITIONS = ["MATCH", "SEPARATE", "UNSURE", "ESCALATE"] as const;
const P3_ACTION_LABELS: Record<string, string> = {
  MATCH: "نفس الشركة",
  SEPARATE: "شركتان مختلفتان",
  UNSURE: "غير متأكد",
  ESCALATE: "تصعيد للمالك",
};

const SHORT_CR_DISPOSITIONS = ["CONFIRMED_VALID_SHORT_CR", "CONFIRMED_ARTIFACT", "UNRESOLVED_ESCALATE"];
const P3_PAGE_SIZE = 100;
const TRIAGE_PAGE_SIZE = 100;

// Reviewer-facing Arabic labels for the underlying stored disposition values.
// The stored API values (CONFIRMED_ARTIFACT / UNRESOLVED_ESCALATE /
// CONFIRMED_VALID_SHORT_CR) are NOT changed; these are display labels only.
const SHORT_CR_ACTION_LABELS: Record<string, string> = {
  CONFIRMED_ARTIFACT: "استبعاد الرقم القصير",
  UNRESOLVED_ESCALATE: "تصعيد للمراجعة",
  CONFIRMED_VALID_SHORT_CR: "اعتماد كـ CR صحيح",
};

// Per-row suggested action (guidance only, never an auto-decision).
function shortCrSuggestedAction(row: { valid_cr_count: number }) {
  return row.valid_cr_count >= 1
    ? { disposition: "CONFIRMED_ARTIFACT", label: "استبعاد الرقم القصير" }
    : { disposition: "UNRESOLVED_ESCALATE", label: "تصعيد للمراجعة" };
}

export default function V3ReviewQueuePage() {
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = useState<TabKey>("p3");
  const queryClient = useQueryClient();
  const [reviewer, setReviewer] = useState("");
  const [p3Batch, setP3Batch] = useState<"priority" | "remainder">("priority");
  const [p3Page, setP3Page] = useState(1);
  const [triagePage, setTriagePage] = useState(1);

  const p3 = useQuery({
    queryKey: ["review-queue", "p3", p3Batch, p3Page],
    queryFn: () => fetchP3Pairs({ status: "pending", batch: p3Batch, page: p3Page, pageSize: P3_PAGE_SIZE }),
    enabled: ready && hasToken,
  });
  const p3Count = useQuery({
    queryKey: ["review-queue", "p3-count"],
    queryFn: fetchP3Count,
    enabled: ready && hasToken,
  });
  const shortCr = useQuery({
    queryKey: ["review-queue", "short-cr"],
    queryFn: fetchShortCR,
    enabled: ready && hasToken,
  });
  const triage = useQuery({
    queryKey: ["review-queue", "triage", triagePage],
    queryFn: () => fetchTriage({ page: triagePage, pageSize: TRIAGE_PAGE_SIZE }),
    enabled: ready && hasToken,
  });
  const triageCounts = useQuery({
    queryKey: ["review-queue", "triage-counts"],
    queryFn: fetchTriageCounts,
    enabled: ready && hasToken,
  });

  useEffect(() => {
    if (!p3.data) return;
    const lastPage = Math.max(1, Math.ceil(p3.data.total / P3_PAGE_SIZE));
    if (p3Page > lastPage) setP3Page(lastPage);
  }, [p3.data, p3Page]);

  useEffect(() => {
    if (!triage.data) return;
    const lastPage = Math.max(1, Math.ceil(triage.data.total / TRIAGE_PAGE_SIZE));
    if (triagePage > lastPage) setTriagePage(lastPage);
  }, [triage.data, triagePage]);

  const p3Disposition = useMutation({
    mutationFn: (vars: { subjectKey: string; disposition: string }) =>
      recordDisposition({
        queueType: "P3_PAIR",
        subjectKey: vars.subjectKey,
        disposition: vars.disposition,
        reviewer: reviewer || "Ragheb (PO)",
        notes: "PHASE7A_PO_DECISION_2026-09-09 D3 human review",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue", "p3"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue", "p3-count"] });
    },
  });

  const shortCrDisposition = useMutation({
    mutationFn: (vars: { subjectKey: string; disposition: string }) =>
      recordDisposition({
        queueType: "SHORT_CR",
        subjectKey: vars.subjectKey,
        disposition: vars.disposition,
        reviewer: reviewer || "Ragheb (PO)",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue", "short-cr"] });
    },
  });

  if (!ready) {
    return <LoadingState />;
  }
  if (!hasToken) {
    return <PermissionState nextPath="/v3/review-queue" />;
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Review Queue"
        description="Phase 7-A — read-only review-queue tooling (dispositions are record-only)"
        actions={
          <div className="flex gap-2">
            <Link
              href="/v3/sales-usability"
              className="rounded border border-border px-3 py-2 text-sm hover:bg-secondary"
            >
              Sales usability
            </Link>
            <Link
              href="/v3/fact-review"
              className="rounded border border-border px-3 py-2 text-sm hover:bg-secondary"
            >
              Review proposed facts
            </Link>
          </div>
        }
      />

      <div className="mb-6 flex gap-2 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === t.key
                ? "border-b-2 border-primary text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "p3" && (
        <section className="space-y-4">
          {p3.isLoading || p3Count.isLoading ? (
            <LoadingState />
          ) : p3.isError || p3Count.isError ? (
            <ErrorState description={(p3.error as Error)?.message ?? "Failed to load P3 pairs"} onRetry={() => { p3.refetch(); p3Count.refetch(); }} />
          ) : (
            <>
              <div className="rounded-lg border bg-card p-4 space-y-2 text-sm">
                <p className="font-semibold">الدفعة الأولى — 114 زوج بنفس النطاق</p>
                <p>الدومين متطابق. هذا أقوى دليل إيجابي في الطابور، لكنه ليس دمجاً تلقائياً. MATCH يسجّل «نفس الشركة» فقط.</p>
                <p>إذا اختلف الاسم جوهرياً أو شككت، صعّد. القرارات تسجيل فقط — لا دمج ولا إنتاج.</p>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <button
                  type="button"
                  onClick={() => { setP3Batch("priority"); setP3Page(1); }}
                  className={`rounded border px-3 py-1 ${p3Batch === "priority" ? "border-primary bg-primary/10" : "border-border"}`}
                >
                  أول دفعة (دومين متطابق)
                </button>
                <button
                  type="button"
                  onClick={() => { setP3Batch("remainder"); setP3Page(1); }}
                  className={`rounded border px-3 py-1 ${p3Batch === "remainder" ? "border-primary bg-primary/10" : "border-border"}`}
                >
                  باقي المعلّق
                </button>
                <span className="text-muted-foreground">
                  في هذه الدفعة: <span className="font-semibold text-foreground">{p3.data?.total ?? "—"}</span>
                </span>
                <label className="ml-auto flex items-center gap-2 text-muted-foreground">
                  <span>المراجع:</span>
                  <input
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    placeholder="Ragheb (PO)"
                    className="rounded border bg-input px-2 py-1 text-sm"
                    style={{ width: 180 }}
                  />
                </label>
                <RefreshCw
                  className="h-4 w-4 cursor-pointer"
                  onClick={() => {
                    p3.refetch();
                    p3Count.refetch();
                  }}
                />
              </div>
              {(p3.data?.items ?? []).length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b text-left text-muted-foreground">
                      <tr>
                        <th className="p-2">الشركة أ</th>
                        <th className="p-2">الشركة ب</th>
                        <th className="p-2">النطاق</th>
                        <th className="p-2">CR</th>
                        <th className="p-2">القرار</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(p3.data?.items ?? []).map((pair) => (
                        <tr key={pair.id} className="border-b align-top">
                          <td className="p-2">
                            <div className="font-medium">{pair.name_a ?? "—"}</div>
                            <div className="text-xs text-muted-foreground">{pair.subject_key}</div>
                          </td>
                          <td className="p-2 font-medium">{pair.name_b ?? "—"}</td>
                          <td className="p-2 font-mono text-xs">
                            {pair.domain_a ?? "—"}
                            {pair.domain_b && pair.domain_b !== pair.domain_a ? ` / ${pair.domain_b}` : ""}
                          </td>
                          <td className="p-2 font-mono text-xs">
                            {pair.cr_a ?? "—"}
                            <br />
                            {pair.cr_b ?? "—"}
                          </td>
                          <td className="p-2">
                            <div className="flex flex-col gap-1">
                              {P3_DISPOSITIONS.map((d) => (
                                <button
                                  key={d}
                                  type="button"
                                  onClick={() => p3Disposition.mutate({ subjectKey: pair.subject_key, disposition: d })}
                                  disabled={p3Disposition.isPending}
                                  className="rounded border border-border bg-card px-2 py-1 text-left text-xs hover:bg-secondary"
                                >
                                  {P3_ACTION_LABELS[d]}
                                </button>
                              ))}
                            </div>
                            {p3Disposition.isError && (
                              <span className="text-xs text-destructive">فشل الحفظ</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState title={p3Batch === "priority" ? "لا بقي أزواج في دفعة الدومين." : "لا بقي أزواج معلّقة في هذا الفلتر."} />
              )}
              {(p3.data?.total ?? 0) > P3_PAGE_SIZE && (
                <div className="flex items-center justify-between border-t border-border pt-3 text-sm text-muted-foreground">
                  <span>
                    عرض {(p3Page - 1) * P3_PAGE_SIZE + 1}–{Math.min(p3Page * P3_PAGE_SIZE, p3.data?.total ?? 0)} من {p3.data?.total ?? 0}
                  </span>
                  <div className="flex items-center gap-2">
                    <span>صفحة {p3Page} من {Math.max(1, Math.ceil((p3.data?.total ?? 0) / P3_PAGE_SIZE))}</span>
                    <button type="button" disabled={p3Page <= 1} onClick={() => setP3Page((page) => Math.max(1, page - 1))} className="rounded border border-border px-3 py-1 disabled:opacity-40">السابق</button>
                    <button type="button" disabled={p3Page >= Math.ceil((p3.data?.total ?? 0) / P3_PAGE_SIZE)} onClick={() => setP3Page((page) => page + 1)} className="rounded border border-border px-3 py-1 disabled:opacity-40">التالي</button>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      )}

      {tab === "short-cr" && (
        <section className="space-y-4">
          {shortCr.isLoading ? (
            <LoadingState />
          ) : shortCr.isError ? (
            <ErrorState description={(shortCr.error as Error)?.message ?? "Failed to load short-CR accounts"} onRetry={() => shortCr.refetch()} />
          ) : (
            <>
              {/* Plain-language guidance panel (non-engineer friendly) */}
              <div className="rounded-lg border bg-card p-4 space-y-2 text-sm">
                <p className="font-semibold">إرشادات المراجعة — أرقام CR القصيرة</p>
                <p>راجع الأرقام القصيرة المرفوضة. إذا كان الرقم القصير مجرد بقايا/كود وليس سجلًا تجاريًا، اختر: <span className="font-medium">استبعاد الرقم القصير</span>.</p>
                <p>إذا لم تستطع الحكم، اختر: <span className="font-medium">تصعيد للمراجعة</span>.</p>
                <p>لا تعتمد رقمًا قصيرًا كسجل تجاري إلا إذا كان لديك مصدر موثوق.</p>
                <div className="mt-2 border-t pt-2 text-xs text-muted-foreground">
                  هذه القرارات تسجيلٌ فقط ولا تغيّر بيانات الشركة ولا الإنتاج.
                </div>
              </div>

              <div className="flex items-center justify-between gap-3">
                <div className="text-sm text-muted-foreground">
                  Total accounts:{" "}
                  <span className="font-semibold text-foreground">{shortCr.data?.total ?? "—"}</span>
                </div>
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>اسم المراجع:</span>
                  <input
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    placeholder="اكتب اسمك هنا (اختياري)"
                    className="rounded border bg-input px-2 py-1 text-sm"
                    style={{ width: 180 }}
                  />
                </label>
              </div>

              {(shortCr.data?.items ?? []).length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b text-left text-muted-foreground">
                      <tr>
                        <th className="p-2">Master Account</th>
                        <th className="p-2">CR_Numbers raw</th>
                        <th className="p-2">Valid CRs</th>
                        <th className="p-2">Rejected tokens</th>
                        <th className="p-2">القرار المقترح</th>
                        <th className="p-2">القرار</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(shortCr.data?.items ?? []).map((row) => {
                        const suggested = shortCrSuggestedAction(row);
                        return (
                          <tr key={row.master_account_id} className="border-b align-top">
                            <td className="p-2">{row.master_account_id}</td>
                            <td className="p-2 font-mono">{row.cr_number_raw}</td>
                            <td className="p-2">{row.valid_cr_count}</td>
                            <td className="p-2 font-mono text-destructive">{row.rejected_tokens.join(", ")}</td>
                            <td className="p-2">
                              <span className="text-xs text-muted-foreground">يُقترح: </span>
                              <span className="text-xs font-medium">{suggested.label}</span>
                            </td>
                            <td className="p-2">
                              <div className="flex flex-col gap-1">
                                {SHORT_CR_DISPOSITIONS.map((d) => (
                                  <button
                                    key={d}
                                    type="button"
                                    onClick={() => shortCrDisposition.mutate({ subjectKey: row.master_account_id, disposition: d })}
                                    disabled={shortCrDisposition.isPending}
                                    className={`rounded border px-2 py-1 text-left text-xs ${
                                      d === suggested.disposition
                                        ? "border-primary bg-primary/10 text-foreground"
                                        : "border-border bg-card text-muted-foreground hover:bg-secondary"
                                    }`}
                                  >
                                    {SHORT_CR_ACTION_LABELS[d] ?? d}
                                  </button>
                                ))}
                              </div>
                              {shortCrDisposition.isPending && (
                                <span className="text-xs text-muted-foreground">جارٍ الحفظ...</span>
                              )}
                              {shortCrDisposition.isError && (
                                <span className="text-xs text-destructive">فشل الحفظ — حاول مجددًا</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState title="No suspicious short-CR accounts found." />
              )}
            </>
          )}
        </section>
      )}

      {tab === "triage" && (
        <section className="space-y-4">
          {triage.isLoading || triageCounts.isLoading ? (
            <LoadingState />
          ) : triage.isError || triageCounts.isError ? (
            <ErrorState description={(triage.error as Error)?.message ?? "Failed to load triage candidates"} onRetry={() => { triage.refetch(); triageCounts.refetch(); }} />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3 lg:grid-cols-5">
                {triageCounts.data &&
                  Object.entries(triageCounts.data.counts).map(([key, count]) => (
                    <div key={key} className="rounded-lg border bg-card p-3">
                      <div className="text-xs text-muted-foreground">{key}</div>
                      <div className="mt-1 text-lg font-semibold">{count}</div>
                    </div>
                  ))}
              </div>
              <div className="text-sm text-muted-foreground">
                Total candidates:{" "}
                <span className="font-semibold text-foreground">{triage.data?.total ?? "—"}</span>
              </div>
              {(triage.data?.items ?? []).length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b text-left text-muted-foreground">
                      <tr>
                        <th className="p-2">Global Company</th>
                        <th className="p-2">Type</th>
                        <th className="p-2">Reason</th>
                        <th className="p-2">Identity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(triage.data?.items ?? []).map((row) => (
                        <tr key={`${row.global_company_id}`} className="border-b">
                          <td className="p-2 font-mono">{row.global_company_id}</td>
                          <td className="p-2">{row.candidate_type}</td>
                          <td className="p-2">{row.reason}</td>
                          <td className="p-2">{row.identity_state ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState title="No triage candidates in the review queue." />
              )}
              {(triage.data?.total ?? 0) > TRIAGE_PAGE_SIZE && (
                <div className="flex items-center justify-between border-t border-border pt-3 text-sm text-muted-foreground">
                  <span>
                    عرض {(triagePage - 1) * TRIAGE_PAGE_SIZE + 1}–{Math.min(triagePage * TRIAGE_PAGE_SIZE, triage.data?.total ?? 0)} من {triage.data?.total ?? 0}
                  </span>
                  <div className="flex items-center gap-2">
                    <span>صفحة {triagePage} من {Math.max(1, Math.ceil((triage.data?.total ?? 0) / TRIAGE_PAGE_SIZE))}</span>
                    <button type="button" disabled={triagePage <= 1} onClick={() => setTriagePage((page) => Math.max(1, page - 1))} className="rounded border border-border px-3 py-1 disabled:opacity-40">السابق</button>
                    <button type="button" disabled={triagePage >= Math.ceil((triage.data?.total ?? 0) / TRIAGE_PAGE_SIZE)} onClick={() => setTriagePage((page) => page + 1)} className="rounded border border-border px-3 py-1 disabled:opacity-40">التالي</button>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
