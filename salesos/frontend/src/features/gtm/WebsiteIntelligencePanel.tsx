"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useRunWebsiteIntelligence,
  useWebsiteIntelligenceDetail,
  useWebsiteIntelligenceList,
  useWebsiteIntelligenceMeta,
} from "@/lib/hooks/websiteIntelligenceQueries";
import type { WebsiteIntelligenceSnapshot } from "@/lib/api";
import {
  WEBSITE_INTEL_HONESTY,
  WEBSITE_INTEL_NON_GOALS,
} from "@/features/gtm/websiteIntelligenceHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S11-07 — Website Intelligence against tip STORY-11-07 HTTP.
 * Fixture analyzer only. feature_ai_copilot False. Not Production GO / RAG GO.
 */
export function WebsiteIntelligencePanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useWebsiteIntelligenceMeta();
  const listQuery = useWebsiteIntelligenceList();
  const runMutation = useRunWebsiteIntelligence();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useWebsiteIntelligenceDetail(selectedId);

  const [url, setUrl] = useState("https://acme.example");
  const [companyName, setCompanyName] = useState("Acme Pilot Co");
  const [pageSnippet, setPageSnippet] = useState("");
  const [analyzerKey, setAnalyzerKey] = useState("");
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const run = searchParams.get("run");
    if (run) setSelectedId(run);
    const u = searchParams.get("url");
    if (u?.trim()) setUrl(u.trim());
    const name = searchParams.get("company_name");
    if (name?.trim()) setCompanyName(name.trim());
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadRun(row: WebsiteIntelligenceSnapshot) {
    setSelectedId(row.id);
    setUrl(String(row.request?.url ?? ""));
    setCompanyName(String(row.request?.company_name ?? ""));
    setPageSnippet(String(row.request?.page_snippet ?? ""));
    setAnalyzerKey(row.analyzer_key || "");
  }

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="website-intel-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="website-intel-honesty"
      >
        {WEBSITE_INTEL_HONESTY} Non-goals: {WEBSITE_INTEL_NON_GOALS.join("; ")}. Not Production GO /
        RAG GO.
      </p>

      {metaQuery.isLoading ? (
        <Spinner />
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="website-intel-meta"
        >
          <p>
            {metaQuery.data.capability} · prompt={metaQuery.data.prompt_id}@
            {metaQuery.data.prompt_version} · analyzers=
            {(metaQuery.data.analyzers_configured ?? []).join(", ") || "—"}
          </p>
          <p data-testid="website-intel-meta-flag">
            feature_ai_copilot={String(metaQuery.data.feature_ai_copilot)} · spend=
            {metaQuery.data.spend_path}
          </p>
          <p data-testid="website-intel-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
        </div>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="website-intel-form"
      >
        <h2 className="text-sm font-semibold">Analyze URL (tip POST)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="min-w-[16rem] flex-1"
            data-testid="website-intel-url"
          />
          <Input
            label="company_name (optional)"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            className="max-w-xs"
            data-testid="website-intel-company"
          />
          <Input
            label="page_snippet (optional)"
            value={pageSnippet}
            onChange={(e) => setPageSnippet(e.target.value)}
            className="min-w-[12rem] flex-1"
            data-testid="website-intel-snippet"
          />
          <Input
            label="analyzer_key (optional)"
            value={analyzerKey}
            onChange={(e) => setAnalyzerKey(e.target.value)}
            className="max-w-xs"
            data-testid="website-intel-analyzer"
            placeholder="fixture_website"
          />
          <Button
            type="button"
            size="sm"
            data-testid="website-intel-run"
            disabled={runMutation.isPending || !url.trim()}
            onClick={() => {
              runMutation.mutate(
                {
                  url: url.trim(),
                  company_name: companyName.trim() || undefined,
                  page_snippet: pageSnippet.trim() || undefined,
                  analyzer_key: analyzerKey.trim() || undefined,
                },
                {
                  onSuccess: (row: WebsiteIntelligenceSnapshot) => {
                    setSelectedId(row.id);
                    toast({
                      title: "Website intelligence run",
                      description: `${row.id} · signals=${row.signal_count} · ${row.analyzer_key}`,
                    });
                  },
                  onError: (err: unknown) => {
                    toast({
                      title: "Analyze failed",
                      description: getApiError(err),
                      variant: "error",
                    });
                  },
                }
              );
            }}
          >
            {runMutation.isPending ? "Analyzing…" : "Run analyze"}
          </Button>
        </div>
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="website-intel-list"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">Snapshots (tip GET)</h2>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            data-testid="website-intel-refresh"
            onClick={() => {
              void metaQuery.refetch();
              void listQuery.refetch();
            }}
          >
            Refresh
          </Button>
        </div>
        {listQuery.isLoading ? (
          <Spinner />
        ) : listQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(listQuery.error)}</p>
        ) : listQuery.data?.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="website-intel-empty">
            No snapshots in memory store yet. Run analyze.
          </p>
        ) : (
          <ul className="space-y-2 text-sm">
            {(listQuery.data ?? []).map((row: WebsiteIntelligenceSnapshot) => (
              <li
                key={row.id}
                className="rounded border border-[var(--border-default)] px-3 py-2"
                data-testid="website-intel-row"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-medium">{String(row.request?.url ?? row.id)}</span>{" "}
                    <span className="font-mono text-xs text-[var(--text-muted)]">
                      {row.analyzer_key} · signals={row.signal_count}
                    </span>
                    {row.summary ? (
                      <p className="text-xs text-[var(--text-muted)]">{row.summary}</p>
                    ) : null}
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    data-testid="website-intel-open"
                    onClick={() => loadRun(row)}
                  >
                    Open
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedId ? (
        <section
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="website-intel-detail"
        >
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Detail (tip GET /{"{id}"})</h2>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              data-testid="website-intel-close"
              onClick={() => setSelectedId(null)}
            >
              Close
            </Button>
          </div>
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">{getApiError(detailQuery.error)}</p>
          ) : active ? (
            <>
              <p className="font-mono text-xs text-[var(--text-muted)]">
                {active.prompt_id}@{active.prompt_version} · {active.spend_path} ·{" "}
                {active.analyzer_key}
              </p>
              {active.signals?.length ? (
                <ul className="space-y-1 text-sm" data-testid="website-intel-signals">
                  {active.signals.map((s) => (
                    <li key={`${s.key}-${s.value}`}>
                      <span className="font-medium">{s.key}</span>: {s.value}{" "}
                      <span className="text-xs text-[var(--text-muted)]">({s.confidence})</span>
                    </li>
                  ))}
                </ul>
              ) : null}
              <pre
                className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
                data-testid="website-intel-detail-result"
              >
                {JSON.stringify(active, null, 2)}
              </pre>
            </>
          ) : null}
          <p className="text-xs text-[var(--text-muted)]">
            Related:{" "}
            <Link href="/gtm/enrichment" className="underline">
              /gtm/enrichment
            </Link>
            . AI Outreach (FE-S11-08) STANDBY until tip HTTP.
          </p>
        </section>
      ) : null}
    </div>
  );
}
