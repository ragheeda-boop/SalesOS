"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useRunVerification,
  useVerificationDetail,
  useVerificationList,
  useVerificationMeta,
} from "@/lib/hooks/verificationQueries";
import type { VerificationRun } from "@/lib/api";
import {
  VERIFICATION_HONESTY,
  VERIFICATION_NON_GOALS,
} from "@/features/gtm/verificationHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S11-06 — Contact Verification against tip STORY-11-06 HTTP.
 * fake_verify connector. Not Production GO / RAG GO.
 */
export function VerificationPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useVerificationMeta();
  const listQuery = useVerificationList();
  const runMutation = useRunVerification();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useVerificationDetail(selectedId);

  const [email, setEmail] = useState("pilot@example.com");
  const [phone, setPhone] = useState("+966500000000");
  const [providerKey, setProviderKey] = useState("");
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const run = searchParams.get("run");
    if (run) setSelectedId(run);
    const e = searchParams.get("email");
    if (e?.trim()) setEmail(e.trim());
    const p = searchParams.get("phone");
    if (p?.trim()) setPhone(p.trim());
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadRun(row: VerificationRun) {
    setSelectedId(row.id);
    setEmail(row.request.email ?? "");
    setPhone(row.request.phone ?? "");
    setProviderKey(row.provider_key ?? row.request.provider_key ?? "");
  }

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="verification-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="verification-honesty"
      >
        {VERIFICATION_HONESTY} Non-goals: {VERIFICATION_NON_GOALS.join("; ")}.
        Not Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="verification-meta"
        >
          <p>
            connectors{" "}
            {(metaQuery.data.connectors_configured ?? []).join(", ") || "—"} ·
            channels {(metaQuery.data.channels ?? []).join(", ")} · statuses{" "}
            {(metaQuery.data.statuses ?? []).join(", ")}
          </p>
          <p data-testid="verification-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
          <p>{metaQuery.data.interface}</p>
        </div>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">
          {getApiError(metaQuery.error)}
        </p>
      ) : (
        <Spinner />
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          data-testid="verification-refresh"
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <span
          className="text-xs text-[var(--text-muted)]"
          data-testid="verification-count"
        >
          {listQuery.data?.length ?? 0} run(s)
        </span>
      </div>

      <ul
        className="max-h-48 space-y-1 overflow-y-auto rounded border border-[var(--border-default)] p-2"
        data-testid="verification-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="text-xs text-[var(--text-muted)]">
            No verification runs yet. Submit email/phone below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li key={row.id}>
              <button
                type="button"
                className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-[var(--bg-muted)] ${
                  selectedId === row.id
                    ? "bg-[var(--bg-muted)] font-medium"
                    : ""
                }`}
                data-testid="verification-row"
                onClick={() => loadRun(row)}
              >
                {row.overall_status} · {row.provider_key || "—"} ·{" "}
                {row.request.email || row.request.phone || row.id}
              </button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="verification-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!email.trim() && !phone.trim()) {
            toast({
              title: "Contact required",
              description: "Provide at least an email or phone.",
              variant: "error",
            });
            return;
          }
          runMutation.mutate(
            {
              email: email.trim() || undefined,
              phone: phone.trim() || undefined,
              provider_key: providerKey.trim() || undefined,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  title: "Verification complete",
                  description: `overall=${row.overall_status} · ${row.verdicts.length} verdict(s)`,
                  variant: "success",
                });
              },
              onError: (err) => {
                toast({
                  title: "Verification failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Run contact verification (tip POST)
        </h2>
        <Input
          label="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          data-testid="verification-email"
        />
        <Input
          label="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          data-testid="verification-phone"
        />
        <Input
          label="provider_key (optional)"
          value={providerKey}
          onChange={(e) => setProviderKey(e.target.value)}
          placeholder="fake_verify"
          data-testid="verification-provider"
        />
        <Button
          type="submit"
          disabled={runMutation.isPending}
          data-testid="verification-run"
        >
          {runMutation.isPending ? "Verifying…" : "Verify"}
        </Button>
      </form>

      {selectedId ? (
        <div
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="verification-detail"
        >
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">
              {getApiError(detailQuery.error)}
            </p>
          ) : active ? (
            <>
              <p
                className="font-mono text-xs text-[var(--text-muted)]"
                data-testid="verification-overall"
              >
                run {active.id} · overall={active.overall_status} · provider{" "}
                {active.provider_key}
              </p>
              <ul
                className="space-y-1 text-sm"
                data-testid="verification-verdicts"
              >
                {active.verdicts.map((v, i) => (
                  <li key={`${v.channel}-${i}`}>
                    {v.channel}: {v.value} → {v.status}
                    {v.reason ? ` (${v.reason})` : ""} · confidence{" "}
                    {v.confidence}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}

      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/gtm/enrichment" className="underline">
          /gtm/enrichment
        </Link>
        {" · "}
        <Link href="/gtm" className="underline">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
