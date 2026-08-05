"use client";

import { useCallback, useMemo, useState, type DragEvent, type ReactNode } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { advanceOpportunity, listOpportunities, type Opportunity } from "@/lib/api";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { openV3AiPopup } from "@/components/v3/V3AiPopup";
import { PageHeader } from "../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

type PipelineStageDef = {
  key: string;
  label: string;
  terminal: boolean;
};

/** Canonical pipeline order — matches backend OpportunityStage.default_pipeline. */
const PIPELINE_STAGES: PipelineStageDef[] = [
  { key: "prospecting", label: "Prospecting", terminal: false },
  { key: "qualification", label: "Qualification", terminal: false },
  { key: "proposal", label: "Proposal", terminal: false },
  { key: "negotiation", label: "Negotiation", terminal: false },
  { key: "closed_won", label: "Closed won", terminal: true },
  { key: "closed_lost", label: "Closed lost", terminal: true },
];

type ViewMode = "board" | "table";

const KNOWN_STAGE_KEYS = new Set<string>(PIPELINE_STAGES.map((s) => s.key));
const TERMINAL_STAGE_KEYS = new Set(PIPELINE_STAGES.filter((s) => s.terminal).map((s) => s.key));

function formatValue(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

function stageLabel(stage: string | undefined): string {
  if (!stage) return "—";
  const known = PIPELINE_STAGES.find((s) => s.key === stage);
  if (known) return known.label;
  return stage.replace(/_/g, " ");
}

function isTerminalStage(stage: string | undefined): boolean {
  return Boolean(stage && TERMINAL_STAGE_KEYS.has(stage));
}

function canAdvanceTo(fromStage: string | undefined, toStage: string): boolean {
  if (!fromStage || fromStage === toStage) return false;
  const fromIdx = PIPELINE_STAGES.findIndex((s) => s.key === fromStage);
  const toIdx = PIPELINE_STAGES.findIndex((s) => s.key === toStage);
  if (fromIdx === -1 || toIdx === -1) return false;
  if (PIPELINE_STAGES[fromIdx]?.terminal) return false;
  // Backend: forward only, or recycle to first stage
  return toIdx >= fromIdx || toIdx === 0;
}

export default function V3CrmPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [view, setView] = useState<ViewMode>("board");
  const [stageFilter, setStageFilter] = useState<string>("all");
  const [q, setQ] = useState("");
  const [moveError, setMoveError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  const advanceMutation = useMutation({
    mutationFn: ({ opportunityId, toStage }: { opportunityId: string; toStage: string }) =>
      advanceOpportunity(opportunityId, toStage),
    onMutate: ({ opportunityId }) => {
      setPendingId(opportunityId);
      setMoveError(null);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
    },
    onError: (err) => {
      setMoveError(err instanceof Error ? err.message : "Could not move deal to that stage.");
    },
    onSettled: () => {
      setPendingId(null);
    },
  });

  const items = useMemo(() => data?.items ?? [], [data?.items]);

  const stagesInData = useMemo(() => {
    const set = new Set<string>();
    for (const opp of items) {
      if (opp.stage) set.add(opp.stage);
    }
    return Array.from(set).sort();
  }, [items]);

  const unknownStages = useMemo(
    () => stagesInData.filter((s) => !KNOWN_STAGE_KEYS.has(s)),
    [stagesInData]
  );

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return items.filter((opp) => {
      if (stageFilter !== "all" && opp.stage !== stageFilter) return false;
      if (!needle) return true;
      const hay = `${opp.name} ${opp.company_name ?? ""} ${opp.stage}`.toLowerCase();
      return hay.includes(needle);
    });
  }, [items, stageFilter, q]);

  const pipelineSum = useMemo(
    () =>
      filtered
        .filter((opp) => opp.stage !== "closed_won" && opp.stage !== "closed_lost")
        .reduce((sum, opp) => sum + (opp.value || 0), 0),
    [filtered]
  );

  const byStage = useMemo(() => {
    const map = new Map<string, Opportunity[]>();
    for (const stage of PIPELINE_STAGES) map.set(stage.key, []);
    for (const stage of unknownStages) map.set(stage, []);
    for (const opp of filtered) {
      const key = opp.stage && map.has(opp.stage) ? opp.stage : "_other";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(opp);
    }
    return map;
  }, [filtered, unknownStages]);

  const moveDeal = useCallback(
    (opportunityId: string, toStage: string) => {
      const opp = items.find((o) => o.id === opportunityId);
      if (!opp) return;
      if (!canAdvanceTo(opp.stage, toStage)) {
        if (opp.stage === toStage) return;
        setMoveError(
          `Invalid move: ${stageLabel(opp.stage)} → ${stageLabel(toStage)}. Forward stages or recycle to Prospecting only.`
        );
        return;
      }
      advanceMutation.mutate({ opportunityId, toStage });
    },
    [advanceMutation, items]
  );

  return (
    <div className={view === "board" ? "mx-auto max-w-[1600px]" : "mx-auto max-w-6xl"}>
      <PageHeader
        title="CRM"
        description="Pipeline board + deal table — Design Program v3. Stage moves call POST /opportunities/{id}/advance. Legacy /pipeline and /opportunities are unchanged."
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => openV3AiPopup({ contextLabel: "CRM pipeline" })}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            >
              Ask AI
            </button>
            <GhostButtonLink href="/v3/companies">Browse companies</GhostButtonLink>
          </div>
        }
      />

      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/crm" />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center">
              <div
                className="inline-flex rounded-[var(--radius-md)] border border-[var(--border-default)] p-0.5"
                role="group"
                aria-label="CRM view"
              >
                <ViewToggleButton active={view === "board"} onClick={() => setView("board")}>
                  Board
                </ViewToggleButton>
                <ViewToggleButton active={view === "table"} onClick={() => setView("table")}>
                  Table
                </ViewToggleButton>
              </div>
              <label className="block min-w-0 flex-1">
                <span className="sr-only">Search deals</span>
                <input
                  type="search"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search deal or company…"
                  className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                />
              </label>
              {view === "table" ? (
                <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <span className="shrink-0 text-[12px] text-[var(--text-muted)]">Stage</span>
                  <select
                    value={stageFilter}
                    onChange={(e) => setStageFilter(e.target.value)}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-2.5 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                  >
                    <option value="all">All stages</option>
                    {PIPELINE_STAGES.map((stage) => (
                      <option key={stage.key} value={stage.key}>
                        {stage.label}
                      </option>
                    ))}
                    {unknownStages.map((stage) => (
                      <option key={stage} value={stage}>
                        {stageLabel(stage)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </div>
            <p className="text-[12px] text-[var(--text-muted)]" aria-live="polite">
              {isFetching && !isLoading ? "Updating… · " : null}
              {!isLoading && !isError
                ? `${filtered.length} deal${filtered.length === 1 ? "" : "s"} · open ${formatValue(pipelineSum)}`
                : null}
            </p>
          </div>

          {moveError ? (
            <div
              className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--status-danger-border,#fecaca)] bg-[var(--status-danger-bg,#fef2f2)] px-3 py-2 text-sm text-[var(--status-danger,#991b1b)]"
              role="alert"
            >
              <p>{moveError}</p>
              <button
                type="button"
                onClick={() => setMoveError(null)}
                className="shrink-0 text-[12px] underline"
              >
                Dismiss
              </button>
            </div>
          ) : null}

          {isLoading ? (
            <LoadingState label="Loading opportunities…" />
          ) : isError ? (
            <ErrorState
              title="Could not load pipeline"
              description={error instanceof Error ? error.message : "Request failed"}
              onRetry={() => void refetch()}
            />
          ) : filtered.length === 0 ? (
            <EmptyState
              title={items.length === 0 ? "No deals yet" : "No matching deals"}
              description={
                items.length === 0
                  ? "Create opportunities from a company record, or open the legacy pipeline when needed."
                  : "Try a different stage or clear the search."
              }
              action={
                q || stageFilter !== "all" ? (
                  <button
                    type="button"
                    onClick={() => {
                      setQ("");
                      setStageFilter("all");
                    }}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                  >
                    Clear filters
                  </button>
                ) : (
                  <GhostButtonLink href="/v3/companies">Find a company</GhostButtonLink>
                )
              }
            />
          ) : view === "board" ? (
            <PipelineBoard
              byStage={byStage}
              unknownStages={unknownStages}
              pendingId={pendingId}
              onMove={moveDeal}
            />
          ) : (
            <DealTable items={filtered} onMove={moveDeal} pendingId={pendingId} />
          )}
        </div>
      )}
    </div>
  );
}

function ViewToggleButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={
        active
          ? "rounded-[calc(var(--radius-md)-2px)] bg-[var(--bg-secondary)] px-3 py-1.5 text-sm font-medium text-[var(--text-primary)]"
          : "rounded-[calc(var(--radius-md)-2px)] px-3 py-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      }
    >
      {children}
    </button>
  );
}

function PipelineBoard({
  byStage,
  unknownStages,
  pendingId,
  onMove,
}: {
  byStage: Map<string, Opportunity[]>;
  unknownStages: string[];
  pendingId: string | null;
  onMove: (opportunityId: string, toStage: string) => void;
}) {
  const columns: { key: string; label: string; terminal?: boolean }[] = [
    ...PIPELINE_STAGES,
    ...unknownStages.map((key) => ({ key, label: stageLabel(key) })),
  ];
  if ((byStage.get("_other") ?? []).length > 0) {
    columns.push({ key: "_other", label: "Other" });
  }

  return (
    <div className="space-y-2">
      <p className="text-[12px] text-[var(--text-muted)]">
        Drag a deal onto another column to advance (or recycle to Prospecting). Terminal stages
        cannot be moved.
      </p>
      <div className="-mx-1 overflow-x-auto pb-2">
        <div className="flex min-w-min gap-3 px-1">
          {columns.map((col) => (
            <BoardColumn
              key={col.key}
              stageKey={col.key}
              label={col.label}
              terminal={Boolean(col.terminal)}
              droppable={col.key !== "_other"}
              items={byStage.get(col.key) ?? []}
              pendingId={pendingId}
              onMove={onMove}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function BoardColumn({
  stageKey,
  label,
  terminal,
  droppable,
  items,
  pendingId,
  onMove,
}: {
  stageKey: string;
  label: string;
  terminal: boolean;
  droppable: boolean;
  items: Opportunity[];
  pendingId: string | null;
  onMove: (opportunityId: string, toStage: string) => void;
}) {
  const [dragOver, setDragOver] = useState(false);
  const colSum = items.reduce((sum, opp) => sum + (opp.value || 0), 0);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    if (!droppable) return;
    e.preventDefault();
    setDragOver(true);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (!droppable) return;
    const oppId = e.dataTransfer.getData("text/plain");
    if (oppId) onMove(oppId, stageKey);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`flex w-[240px] shrink-0 flex-col rounded-[var(--radius-lg)] border bg-[var(--bg-secondary)] ${
        dragOver
          ? "border-[var(--muhide-orange)] bg-[color-mix(in_srgb,var(--muhide-orange)_8%,var(--bg-secondary))]"
          : "border-[var(--border-default)]"
      }`}
    >
      <div className="flex items-center justify-between gap-2 border-b border-[var(--border-default)] px-3 py-2.5">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-[var(--text-primary)]">{label}</p>
          <p className="text-[11px] text-[var(--text-muted)]">
            {items.length} · {formatValue(colSum)}
          </p>
        </div>
        {terminal ? (
          <span className="shrink-0 rounded-full border border-[var(--border-default)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">
            Done
          </span>
        ) : null}
      </div>
      <div className="flex max-h-[min(70vh,640px)] flex-col gap-2 overflow-y-auto p-2">
        {items.length === 0 ? (
          <p className="px-1 py-6 text-center text-[12px] text-[var(--text-muted)]">Empty</p>
        ) : (
          items.map((opp) => (
            <DealCard
              key={opp.id}
              opportunity={opp}
              draggable={!terminal && !isTerminalStage(opp.stage)}
              pending={pendingId === opp.id}
            />
          ))
        )}
      </div>
    </div>
  );
}

function DealCard({
  opportunity,
  draggable,
  pending,
}: {
  opportunity: Opportunity;
  draggable: boolean;
  pending: boolean;
}) {
  const [dragging, setDragging] = useState(false);

  return (
    <div
      draggable={draggable}
      onDragStart={(e) => {
        if (!draggable) {
          e.preventDefault();
          return;
        }
        e.dataTransfer.setData("text/plain", opportunity.id);
        e.dataTransfer.effectAllowed = "move";
        setDragging(true);
      }}
      onDragEnd={() => setDragging(false)}
      className={`rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 shadow-[var(--shadow-sm,none)] ${
        draggable ? "cursor-grab active:cursor-grabbing" : ""
      } ${dragging || pending ? "opacity-60" : ""} ${pending ? "ring-2 ring-[var(--muhide-orange)]/40" : ""}`}
    >
      <Link
        href={`/v3/crm/${opportunity.id}`}
        className="block text-sm font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        onClick={(e) => {
          if (dragging) e.preventDefault();
        }}
      >
        {opportunity.name}
      </Link>
      <p className="mt-1 text-[12px] tabular-nums text-[var(--text-secondary)]">
        {formatValue(opportunity.value)}
      </p>
      {opportunity.company_id ? (
        <Link
          href={`/v3/companies/${opportunity.company_id}`}
          className="mt-1 block truncate text-[12px] text-[var(--text-muted)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          {opportunity.company_name || "Company"}
        </Link>
      ) : opportunity.company_name ? (
        <p className="mt-1 truncate text-[12px] text-[var(--text-muted)]">
          {opportunity.company_name}
        </p>
      ) : null}
    </div>
  );
}

function DealTable({
  items,
  onMove,
  pendingId,
}: {
  items: Opportunity[];
  onMove: (opportunityId: string, toStage: string) => void;
  pendingId: string | null;
}) {
  return (
    <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
            <tr>
              <th scope="col" className="px-3 py-2.5 font-medium">
                Deal
              </th>
              <th scope="col" className="px-3 py-2.5 font-medium">
                Company
              </th>
              <th scope="col" className="px-3 py-2.5 font-medium">
                Stage
              </th>
              <th scope="col" className="px-3 py-2.5 font-medium">
                Value
              </th>
              <th scope="col" className="px-3 py-2.5 font-medium">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((opp) => {
              const isTerminal = isTerminalStage(opp.stage);
              return (
                <tr
                  key={opp.id}
                  className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2.5 font-medium text-[var(--text-primary)]">
                    <Link
                      href={`/v3/crm/${opp.id}`}
                      className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {opp.name}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                    {opp.company_id ? (
                      <Link
                        href={`/v3/companies/${opp.company_id}`}
                        className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                      >
                        {opp.company_name || "View company"}
                      </Link>
                    ) : (
                      opp.company_name || "—"
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                    {isTerminal ? (
                      <span className="capitalize">{stageLabel(opp.stage)}</span>
                    ) : (
                      <select
                        value={opp.stage}
                        disabled={pendingId === opp.id}
                        onChange={(e) => {
                          const next = e.target.value;
                          if (next !== opp.stage) onMove(opp.id, next);
                        }}
                        aria-label={`Move ${opp.name} to stage`}
                        className="max-w-[160px] rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-sm capitalize outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] disabled:opacity-60"
                      >
                        {!KNOWN_STAGE_KEYS.has(opp.stage) ? (
                          <option value={opp.stage}>{stageLabel(opp.stage)}</option>
                        ) : null}
                        {PIPELINE_STAGES.map((stage) => (
                          <option
                            key={stage.key}
                            value={stage.key}
                            disabled={
                              stage.key !== opp.stage && !canAdvanceTo(opp.stage, stage.key)
                            }
                          >
                            {stage.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-3 py-2.5 tabular-nums text-[var(--text-secondary)]">
                    {formatValue(opp.value)}
                  </td>
                  <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                    {opp.status?.replace(/_/g, " ") || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
