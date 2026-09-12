"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listOpportunities } from "@/lib/api";
import { listQuotes } from "@/lib/api/quotes";
import { createProposal } from "@/lib/api/proposals";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create proposals.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create proposal.";
}

function dealLabel(name: string | undefined, id: string): string {
  return name?.trim() || id;
}

function quoteLabel(quote: {
  id: string;
  status?: string;
  version?: number;
}): string {
  const status = quote.status?.trim();
  const version = quote.version != null ? `v${quote.version}` : "";
  return [quote.id, status, version].filter(Boolean).join(" · ");
}

export function CreateProposalForm({
  opportunityId: lockedOpportunityId,
  onCancel,
}: {
  opportunityId?: string;
  onCancel?: () => void;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [pickedOpportunityId, setPickedOpportunityId] = useState("");
  const [pickedQuoteId, setPickedQuoteId] = useState("");

  const opportunityId = lockedOpportunityId || pickedOpportunityId;
  const needsDealPicker = !lockedOpportunityId;

  const dealsQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 10_000,
    enabled: needsDealPicker,
  });

  const quotesQuery = useQuery({
    queryKey: ["quotes", "list", opportunityId],
    queryFn: () => listQuotes({ opportunity_id: opportunityId }, getTenantId()),
    staleTime: 10_000,
    enabled: Boolean(opportunityId),
  });

  const deals = dealsQuery.data?.items ?? [];
  const quotes = quotesQuery.data?.items ?? [];
  const canSubmit = Boolean(opportunityId && pickedQuoteId);

  const createMutation = useMutation({
    mutationFn: () => createProposal(getTenantId(), opportunityId, pickedQuoteId),
    onSuccess: (proposal: { id?: string }) => {
      void queryClient.invalidateQueries({ queryKey: ["proposals"] });
      if (proposal?.id) {
        router.push(`/v3/proposals/${proposal.id}`);
      }
    },
  });

  return (
    <form
      className="space-y-3 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!canSubmit || createMutation.isPending) return;
        createMutation.mutate();
      }}
    >
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New proposal</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/proposals — required opportunity_id + quote_id query. Null body. No sections
        editor here. Needs a quote first.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {needsDealPicker ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Deal</span>
            <select
              value={pickedOpportunityId}
              onChange={(e) => {
                setPickedOpportunityId(e.target.value);
                setPickedQuoteId("");
              }}
              required
              className={INPUT_CLASS}
              data-testid="create-proposal-opportunity"
              disabled={dealsQuery.isLoading || deals.length === 0}
            >
              <option value="">
                {dealsQuery.isLoading ? "Loading deals…" : "Select a deal"}
              </option>
              {deals.map((deal) => (
                <option key={deal.id} value={deal.id}>
                  {dealLabel(deal.name, deal.id)}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <p
            className="self-end text-[12px] text-[var(--text-muted)]"
            data-testid="create-proposal-opportunity-locked"
          >
            opportunity_id locked to this deal
          </p>
        )}
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Quote</span>
          <select
            value={pickedQuoteId}
            onChange={(e) => setPickedQuoteId(e.target.value)}
            required
            className={INPUT_CLASS}
            data-testid="create-proposal-quote"
            disabled={!opportunityId || quotesQuery.isLoading || quotes.length === 0}
          >
            <option value="">
              {!opportunityId
                ? "Select a deal first"
                : quotesQuery.isLoading
                  ? "Loading quotes…"
                  : "Select a quote"}
            </option>
            {quotes.map((quote) => (
              <option key={quote.id} value={quote.id}>
                {quoteLabel(quote)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {needsDealPicker && dealsQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load deals for opportunity_id. Retry or create a deal in v3 first.
        </p>
      ) : null}
      {needsDealPicker && !dealsQuery.isLoading && !dealsQuery.isError && deals.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-proposal-no-deals">
          No deals in this tenant. Create a deal first — POST /api/v1/proposals requires
          opportunity_id.{" "}
          <Link
            href="/v3/crm"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create deal
          </Link>
        </p>
      ) : null}
      {opportunityId && quotesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load quotes for this deal. Retry or create a quote in v3 first.
        </p>
      ) : null}
      {opportunityId &&
      !quotesQuery.isLoading &&
      !quotesQuery.isError &&
      quotes.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-proposal-no-quotes">
          No quotes for this deal. POST /api/v1/proposals requires quote_id.{" "}
          <Link
            href="/v3/quotes"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create quote
          </Link>
        </p>
      ) : null}
      {createMutation.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          {createErrorMessage(createMutation.error)}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={!canSubmit || createMutation.isPending}
          className="rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          data-testid="create-proposal-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create proposal"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
