"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCreateOutreachDraft,
  useOutreachDetail,
  useOutreachList,
  useOutreachMeta,
} from "@/lib/hooks/outreachQueries";
import type { OutreachDraft } from "@/lib/api";
import { OUTREACH_HONESTY, OUTREACH_NON_GOALS } from "@/features/gtm/outreachHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S11-08 — AI Outreach against tip STORY-11-08 HTTP.
 * Fixture generator; draft_only. feature_ai_copilot False. Not Production GO.
 */
export function OutreachPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useOutreachMeta();
  const listQuery = useOutreachList();
  const createMutation = useCreateOutreachDraft();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useOutreachDetail(selectedId);

  const [companyName, setCompanyName] = useState("Acme Pilot Co");
  const [contactName, setContactName] = useState("");
  const [contactTitle, setContactTitle] = useState("");
  const [channel, setChannel] = useState("email");
  const [intent, setIntent] = useState("intro");
  const [valueProp, setValueProp] = useState("");
  const [websiteSummary, setWebsiteSummary] = useState("");
  const [icpNotes, setIcpNotes] = useState("");
  const [generatorKey, setGeneratorKey] = useState("");
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const run = searchParams.get("run");
    if (run) setSelectedId(run);
    const name = searchParams.get("company_name");
    if (name?.trim()) setCompanyName(name.trim());
    const summary = searchParams.get("website_summary");
    if (summary?.trim()) setWebsiteSummary(summary.trim());
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadDraft(row: OutreachDraft) {
    setSelectedId(row.id);
    const req = row.request ?? {};
    setCompanyName(String(req.company_name ?? ""));
    setContactName(String(req.contact_name ?? ""));
    setContactTitle(String(req.contact_title ?? ""));
    setChannel(row.channel || "email");
    setIntent(String(req.intent ?? "intro"));
    setValueProp(String(req.value_prop ?? ""));
    setWebsiteSummary(String(req.website_summary ?? ""));
    setIcpNotes(String(req.icp_notes ?? ""));
    setGeneratorKey(row.generator_key || "");
  }

  const active = detailQuery.data;
  const channels = metaQuery.data?.channels ?? ["email"];
  const intents = metaQuery.data?.intents ?? ["intro", "follow_up", "breakup"];

  return (
    <div className="space-y-4" data-testid="outreach-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="outreach-honesty"
      >
        {OUTREACH_HONESTY} Non-goals: {OUTREACH_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
      </p>

      {metaQuery.isLoading ? (
        <Spinner />
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="outreach-meta"
        >
          <p>
            {metaQuery.data.capability} · prompt={metaQuery.data.prompt_id}@
            {metaQuery.data.prompt_version} · delivery=
            {metaQuery.data.delivery_status} · generators=
            {(metaQuery.data.generators_configured ?? []).join(", ") || "—"}
          </p>
          <p data-testid="outreach-meta-flag">
            feature_ai_copilot={String(metaQuery.data.feature_ai_copilot)} · channels=
            {(metaQuery.data.channels ?? []).join(", ")} · intents=
            {(metaQuery.data.intents ?? []).join(", ")}
          </p>
          <p data-testid="outreach-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
        </div>
      ) : null}

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="outreach-form"
      >
        <h2 className="text-sm font-semibold">Draft outreach (tip POST)</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="company_name"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            className="max-w-xs"
            data-testid="outreach-company"
          />
          <Input
            label="contact_name (optional)"
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            className="max-w-xs"
            data-testid="outreach-contact"
          />
          <Input
            label="contact_title (optional)"
            value={contactTitle}
            onChange={(e) => setContactTitle(e.target.value)}
            className="max-w-xs"
            data-testid="outreach-title"
          />
          <label className="block text-xs text-[var(--text-muted)]">
            channel
            <select
              className="mt-1 block w-full max-w-xs rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 text-sm"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              data-testid="outreach-channel"
            >
              {channels.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs text-[var(--text-muted)]">
            intent
            <select
              className="mt-1 block w-full max-w-xs rounded border border-[var(--border-default)] bg-transparent px-2 py-1.5 text-sm"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              data-testid="outreach-intent"
            >
              {intents.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="value_prop (optional)"
            value={valueProp}
            onChange={(e) => setValueProp(e.target.value)}
            className="min-w-[12rem] flex-1"
            data-testid="outreach-value-prop"
          />
          <Input
            label="website_summary (optional)"
            value={websiteSummary}
            onChange={(e) => setWebsiteSummary(e.target.value)}
            className="min-w-[12rem] flex-1"
            data-testid="outreach-website-summary"
          />
          <Input
            label="icp_notes (optional)"
            value={icpNotes}
            onChange={(e) => setIcpNotes(e.target.value)}
            className="min-w-[12rem] flex-1"
            data-testid="outreach-icp-notes"
          />
          <Input
            label="generator_key (optional)"
            value={generatorKey}
            onChange={(e) => setGeneratorKey(e.target.value)}
            className="max-w-xs"
            data-testid="outreach-generator"
            placeholder="fixture_outreach"
          />
          <Button
            type="button"
            size="sm"
            data-testid="outreach-create"
            disabled={createMutation.isPending || !companyName.trim()}
            onClick={() => {
              createMutation.mutate(
                {
                  company_name: companyName.trim(),
                  contact_name: contactName.trim() || undefined,
                  contact_title: contactTitle.trim() || undefined,
                  channel: channel.trim() || "email",
                  intent: intent.trim() || "intro",
                  value_prop: valueProp.trim() || undefined,
                  website_summary: websiteSummary.trim() || undefined,
                  icp_notes: icpNotes.trim() || undefined,
                  generator_key: generatorKey.trim() || undefined,
                },
                {
                  onSuccess: (row: OutreachDraft) => {
                    setSelectedId(row.id);
                    toast({
                      title: "Outreach draft created",
                      description: `${row.id} · ${row.delivery_status} · ${row.channel}`,
                    });
                  },
                  onError: (err: unknown) => {
                    toast({
                      title: "Draft failed",
                      description: getApiError(err),
                      variant: "error",
                    });
                  },
                }
              );
            }}
          >
            {createMutation.isPending ? "Drafting…" : "Create draft"}
          </Button>
        </div>
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="outreach-list"
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">Drafts (tip GET)</h2>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            data-testid="outreach-refresh"
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
          <p className="text-sm text-[var(--text-muted)]" data-testid="outreach-empty">
            No drafts in memory store yet. Create draft.
          </p>
        ) : (
          <ul className="space-y-2 text-sm">
            {(listQuery.data ?? []).map((row: OutreachDraft) => (
              <li
                key={row.id}
                className="rounded border border-[var(--border-default)] px-3 py-2"
                data-testid="outreach-row"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-medium">
                      {row.subject || String(row.request?.company_name ?? row.id)}
                    </span>{" "}
                    <span className="font-mono text-xs text-[var(--text-muted)]">
                      {row.channel} · {row.delivery_status} · {row.generator_key}
                    </span>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    data-testid="outreach-open"
                    onClick={() => loadDraft(row)}
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
          data-testid="outreach-detail"
        >
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Detail (tip GET /{"{id}"})</h2>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              data-testid="outreach-close"
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
                {active.delivery_status}
              </p>
              {active.subject ? (
                <p className="text-sm" data-testid="outreach-subject">
                  <span className="font-medium">Subject:</span> {active.subject}
                </p>
              ) : null}
              {active.body ? (
                <pre
                  className="whitespace-pre-wrap rounded bg-[var(--bg-muted)] p-2 text-sm"
                  data-testid="outreach-body"
                >
                  {active.body}
                </pre>
              ) : null}
              <pre
                className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
                data-testid="outreach-detail-result"
              >
                {JSON.stringify(active, null, 2)}
              </pre>
            </>
          ) : null}
          <p className="text-xs text-[var(--text-muted)]">
            Related:{" "}
            <Link href="/gtm/website-intelligence" className="underline">
              /gtm/website-intelligence
            </Link>{" "}
            ·{" "}
            <Link href="/gtm/sequences" className="underline">
              /gtm/sequences
            </Link>
            . No live send.
          </p>
        </section>
      ) : null}
    </div>
  );
}
