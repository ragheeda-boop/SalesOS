"use client";

import Link from "next/link";
import { useState } from "react";
import type { AxiosError } from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import {
  decideFactProposal,
  fetchFactProposals,
  type FactDecision,
  type FactProposal,
  type FactProposalStatus,
} from "@/lib/factReviewQueries";

const PAGE_SIZE = 50;

const STATUS_LABELS: Record<FactProposalStatus, string> = {
  PROPOSED: "بانتظار المراجعة",
  APPROVED: "تمت الموافقة",
  REJECTED: "مرفوض",
  DISMISSED: "مستبعد",
  APPLIED: "مطبّق",
  SUPERSEDED: "استُبدل",
  STALE: "قديم",
};

function displayValue(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value) ?? String(value);
  } catch {
    return String(value);
  }
}

function evidenceLabel(item: FactProposal["evidence_snapshot"][number]): string {
  const source = item.source?.source_name || item.source?.source_domain || item.source?.source_type;
  return [source, item.evidence_kind, item.description].filter(Boolean).join(" · ");
}

export default function FactReviewPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<FactProposalStatus>("PROPOSED");
  const [offset, setOffset] = useState(0);
  const [reasons, setReasons] = useState<Record<string, string>>({});

  const proposals = useQuery({
    queryKey: ["fact-proposals", status, offset],
    queryFn: () => fetchFactProposals({ status, limit: PAGE_SIZE, offset }),
    enabled: ready && hasToken,
  });

  const decision = useMutation({
    mutationFn: (input: { id: string; decision: FactDecision; reason: string }) =>
      decideFactProposal(input),
    onSuccess: (_result, variables) => {
      setReasons((current) => ({ ...current, [variables.id]: "" }));
      void queryClient.invalidateQueries({ queryKey: ["fact-proposals"] });
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/fact-review" />;

  const errorStatus = (proposals.error as AxiosError | null)?.response?.status;
  const decisionErrorStatus = (decision.error as AxiosError | null)?.response?.status;
  const items = proposals.data?.items ?? [];

  function submit(fact: FactProposal, action: FactDecision) {
    const reason = reasons[fact.id]?.trim();
    if (!reason) return;
    decision.mutate({ id: fact.id, decision: action, reason });
  }

  return (
    <main className="p-6">
      <PageHeader
        title="Fact Review"
        description="مراجعة اقتراحات تحديث بيانات الشركات وجهات الاتصال، مع حفظ الدليل والقرار."
        actions={
          <Link
            href="/v3/review-queue"
            className="rounded border border-border px-3 py-2 text-sm hover:bg-secondary"
          >
            مراجعة مرشحي الهوية
          </Link>
        }
      />

      <div className="mb-5 rounded-lg border border-[var(--status-warning-border)] bg-[var(--status-warning-bg)] p-4 text-sm text-[var(--status-warning-text)]">
        الموافقة تسجل القرار فقط. لن تتغير بيانات Company أو Contact تلقائيًا من هذه الشاشة.
      </div>

      <section className="space-y-4" aria-label="Fact proposals">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            الحالة
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as FactProposalStatus);
                setOffset(0);
              }}
              className="rounded border bg-background px-3 py-2"
            >
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <span className="text-sm text-muted-foreground">
            {items.length} نتيجة في هذه الصفحة
          </span>
          <button
            type="button"
            onClick={() => void proposals.refetch()}
            className="ml-auto inline-flex items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-secondary"
            aria-label="تحديث القائمة"
          >
            <RefreshCw className="h-4 w-4" /> تحديث
          </button>
        </div>

        {proposals.isLoading ? (
          <LoadingState />
        ) : proposals.isError ? (
          <ErrorState
            title={errorStatus === 403 ? "صلاحية المراجعة مطلوبة" : "تعذر تحميل الاقتراحات"}
            description={
              errorStatus === 403
                ? "هذه الأداة متاحة للمستخدمين المخولين بمراجعة البيانات الرئيسية."
                : (proposals.error as Error).message
            }
            onRetry={() => void proposals.refetch()}
          />
        ) : items.length === 0 ? (
          <EmptyState
            title="لا توجد اقتراحات بهذه الحالة"
            description="ستظهر الاقتراحات هنا بعد تسجيلها عبر مسار إثراء معتمد."
          />
        ) : (
          <div className="space-y-4">
            {items.map((fact) => (
              <article key={fact.id} className="rounded-lg border bg-card p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs text-muted-foreground">
                      {fact.subject_type === "company" ? "شركة" : "جهة اتصال"} · {fact.subject_id}
                    </p>
                    <h2 className="mt-1 text-lg font-semibold">
                      {fact.field_name}: {displayValue(fact.proposed_value)}
                    </h2>
                  </div>
                  <div className="text-right text-sm">
                    <span className="rounded-full border px-2 py-1">{STATUS_LABELS[fact.status]}</span>
                    <p className="mt-2 text-muted-foreground">
                      الثقة {Math.round(fact.score * 100)}% · {fact.evidence_band}
                    </p>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium">الأدلة</p>
                  {fact.evidence_snapshot.length > 0 ? (
                    <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                      {fact.evidence_snapshot.map((item, index) => (
                        <li key={item.id ?? `${fact.id}-evidence-${index}`}>
                          {evidenceLabel(item) || "دليل مسجل"}
                          {typeof item.confidence === "number"
                            ? ` · ثقة المصدر ${Math.round(item.confidence * 100)}%`
                            : ""}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">لا توجد تفاصيل دليل محفوظة.</p>
                  )}
                  <p className="text-xs text-muted-foreground">{fact.decision_reason}</p>
                </div>

                {fact.status === "PROPOSED" ? (
                  <div className="mt-4 space-y-3 border-t pt-4">
                    <label className="block text-sm font-medium" htmlFor={`reason-${fact.id}`}>
                      سبب القرار
                    </label>
                    <textarea
                      id={`reason-${fact.id}`}
                      value={reasons[fact.id] ?? ""}
                      onChange={(event) =>
                        setReasons((current) => ({ ...current, [fact.id]: event.target.value }))
                      }
                      rows={2}
                      maxLength={2000}
                      className="w-full rounded border bg-background p-2 text-sm"
                      placeholder="اكتب ما راجعته ولماذا اتخذت هذا القرار"
                    />
                    <div className="flex flex-wrap gap-2">
                      {([
                        ["approve", "موافقة"],
                        ["reject", "رفض"],
                        ["dismiss", "استبعاد"],
                      ] as const).map(([action, label]) => (
                        <button
                          key={action}
                          type="button"
                          onClick={() => submit(fact, action)}
                          disabled={!reasons[fact.id]?.trim() || decision.isPending}
                          className="rounded border px-3 py-2 text-sm hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {decision.isPending && decision.variables?.id === fact.id
                            ? "جارٍ الحفظ…"
                            : label}
                        </button>
                      ))}
                    </div>
                    {decision.isError && decision.variables?.id === fact.id ? (
                      <p className="text-sm text-destructive" role="alert">
                        {decisionErrorStatus === 409
                          ? "تغيرت حالة الاقتراح. حدّث القائمة قبل المحاولة مجددًا."
                          : "تعذر تسجيل القرار. تحقق من الصلاحية ثم أعد المحاولة."}
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="mt-4 border-t pt-3 text-sm text-muted-foreground">
                    المراجع: {fact.reviewer_id ?? "—"} · {fact.reviewed_at ?? "—"}
                  </p>
                )}
              </article>
            ))}
          </div>
        )}

        <div className="flex justify-between">
          <button
            type="button"
            onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
            disabled={offset === 0 || proposals.isFetching}
            className="rounded border px-3 py-2 text-sm disabled:opacity-50"
          >
            السابق
          </button>
          <button
            type="button"
            onClick={() => setOffset((value) => value + PAGE_SIZE)}
            disabled={items.length < PAGE_SIZE || proposals.isFetching}
            className="rounded border px-3 py-2 text-sm disabled:opacity-50"
          >
            التالي
          </button>
        </div>
      </section>
    </main>
  );
}
