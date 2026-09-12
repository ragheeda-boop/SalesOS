"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listOpportunities } from "@/lib/api";
import { createContract } from "@/lib/api/contracts";
import { listQuotes } from "@/lib/api/quotes";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create contracts.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create contract.";
}

function dealLabel(name: string | undefined, id: string): string {
  return name?.trim() || id;
}

function quoteLabel(quote: {
  id: string;
  title?: string;
  status?: string;
  version?: number;
}): string {
  const title = quote.title?.trim();
  const status = quote.status?.trim();
  const version = quote.version != null ? `v${quote.version}` : "";
  return [title || quote.id, status, version].filter(Boolean).join(" · ");
}

export function CreateContractForm({ onCancel }: { onCancel?: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [pickedOpportunityId, setPickedOpportunityId] = useState("");
  const [pickedQuoteId, setPickedQuoteId] = useState("");

  const dealsQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 10_000,
  });

  const quotesQuery = useQuery({
    queryKey: ["quotes", "list", pickedOpportunityId],
    queryFn: () => listQuotes({ opportunity_id: pickedOpportunityId }, getTenantId()),
    staleTime: 10_000,
    enabled: Boolean(pickedOpportunityId),
  });

  const deals = dealsQuery.data?.items ?? [];
  const quotes = quotesQuery.data?.items ?? [];
  const canSubmit = Boolean(pickedOpportunityId);

  const createMutation = useMutation({
    mutationFn: () =>
      createContract(
        {
          opportunity_id: pickedOpportunityId,
          ...(pickedQuoteId ? { quote_id: pickedQuoteId } : {}),
          ...(title.trim() ? { title: title.trim() } : {}),
        },
        getTenantId()
      ),
    onSuccess: (contract: { id?: string }) => {
      void queryClient.invalidateQueries({ queryKey: ["contracts"] });
      if (contract?.id) {
        router.push(`/v3/contracts/${contract.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New contract</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/contracts — required opportunity_id. quote_id and title are optional. No
        sign or activate here.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
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
            data-testid="create-contract-opportunity"
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
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">
            Title (optional)
          </span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-contract-title"
          />
        </label>
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">
            Quote (optional)
          </span>
          <select
            value={pickedQuoteId}
            onChange={(e) => setPickedQuoteId(e.target.value)}
            className={INPUT_CLASS}
            data-testid="create-contract-quote"
            disabled={!pickedOpportunityId || quotesQuery.isLoading}
          >
            <option value="">
              {!pickedOpportunityId
                ? "Select a deal first"
                : quotesQuery.isLoading
                  ? "Loading quotes…"
                  : "None — opportunity_id only"}
            </option>
            {quotes.map((quote) => (
              <option key={quote.id} value={quote.id}>
                {quoteLabel(quote)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {dealsQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load deals for opportunity_id. Retry or create a deal in v3 first.
        </p>
      ) : null}
      {!dealsQuery.isLoading && !dealsQuery.isError && deals.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-contract-no-deals">
          No deals in this tenant. Create a deal first — POST /api/v1/contracts requires
          opportunity_id.{" "}
          <Link
            href="/v3/crm"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create deal
          </Link>
        </p>
      ) : null}
      {pickedOpportunityId && quotesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load quotes for this deal. quote_id is optional — you can still create.
        </p>
      ) : null}
      {pickedOpportunityId &&
      !quotesQuery.isLoading &&
      !quotesQuery.isError &&
      quotes.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-contract-no-quotes">
          No quotes for this deal. quote_id is optional.{" "}
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
          data-testid="create-contract-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create contract"}
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
