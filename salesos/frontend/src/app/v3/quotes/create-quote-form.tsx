"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listOpportunities } from "@/lib/api";
import { createQuote } from "@/lib/api/quotes";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create quotes.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create quote.";
}

function dealLabel(name: string | undefined, id: string): string {
  return name?.trim() || id;
}

export function CreateQuoteForm({
  opportunityId: lockedOpportunityId,
  onCancel,
}: {
  opportunityId?: string;
  onCancel?: () => void;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [pickedOpportunityId, setPickedOpportunityId] = useState("");

  const opportunityId = lockedOpportunityId || pickedOpportunityId;
  const needsPicker = !lockedOpportunityId;

  const dealsQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 10_000,
    enabled: needsPicker,
  });

  const deals = dealsQuery.data?.items ?? [];
  const canSubmit = Boolean(title.trim() && opportunityId);

  const createMutation = useMutation({
    mutationFn: () => createQuote(getTenantId(), opportunityId, title.trim()),
    onSuccess: (quote: { id?: string }) => {
      void queryClient.invalidateQueries({ queryKey: ["quotes"] });
      if (quote?.id) {
        router.push(`/v3/quotes/${quote.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New quote</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/quotes — required opportunity_id. Title defaults to Quote on the server if
        omitted; this form sends the title you enter. No line items here.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Quote title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-quote-title"
          />
        </label>
        {needsPicker ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Deal</span>
            <select
              value={pickedOpportunityId}
              onChange={(e) => setPickedOpportunityId(e.target.value)}
              required
              className={INPUT_CLASS}
              data-testid="create-quote-opportunity"
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
            data-testid="create-quote-opportunity-locked"
          >
            opportunity_id locked to this deal
          </p>
        )}
      </div>
      {needsPicker && dealsQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load deals for opportunity_id. Retry or create a deal in v3 first.
        </p>
      ) : null}
      {needsPicker && !dealsQuery.isLoading && !dealsQuery.isError && deals.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-quote-no-deals">
          No deals in this tenant. Create a deal first — POST /api/v1/quotes requires
          opportunity_id.{" "}
          <Link
            href="/v3/crm"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create deal
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
          data-testid="create-quote-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create quote"}
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
