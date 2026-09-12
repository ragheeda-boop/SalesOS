"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listOpportunities } from "@/lib/api";
import { listQuotes } from "@/lib/api/quotes";
import { listProposals } from "@/lib/api/proposals";
import { createReview } from "@/lib/api/reviews";
import { opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

const REVIEW_TYPES = [
  "deal_review",
  "manager_review",
  "exception_review",
  "quote_review",
  "proposal_review",
] as const;

type ReviewType = (typeof REVIEW_TYPES)[number];
type TargetType = "opportunity" | "quote" | "proposal";

function defaultTargetType(reviewType: ReviewType): TargetType {
  if (reviewType === "quote_review") return "quote";
  if (reviewType === "proposal_review") return "proposal";
  return "opportunity";
}

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create reviews.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create review.";
}

function dealLabel(name: string | undefined, id: string): string {
  return name?.trim() || id;
}

function quoteLabel(quote: { id: string; status?: string; version?: number }): string {
  const status = quote.status?.trim();
  const version = quote.version != null ? `v${quote.version}` : "";
  return [quote.id, status, version].filter(Boolean).join(" · ");
}

function proposalLabel(proposal: { id: string; title?: string; status?: string }): string {
  return [proposal.title?.trim() || proposal.id, proposal.status].filter(Boolean).join(" · ");
}

export function CreateReviewForm({ onCancel }: { onCancel?: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [reviewType, setReviewType] = useState<ReviewType | "">("");
  const [targetType, setTargetType] = useState<TargetType | "">("");
  const [pickedOpportunityId, setPickedOpportunityId] = useState("");
  const [pickedTargetId, setPickedTargetId] = useState("");

  const needsDealFilter = targetType === "quote" || targetType === "proposal";
  const targetId =
    targetType === "opportunity" ? pickedOpportunityId : pickedTargetId;

  const dealsQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 10_000,
    enabled: Boolean(targetType),
  });

  const quotesQuery = useQuery({
    queryKey: ["quotes", "list", pickedOpportunityId],
    queryFn: () => listQuotes({ opportunity_id: pickedOpportunityId }, getTenantId()),
    staleTime: 10_000,
    enabled: targetType === "quote" && Boolean(pickedOpportunityId),
  });

  const proposalsQuery = useQuery({
    queryKey: ["proposals", "list", pickedOpportunityId],
    queryFn: () => listProposals({ opportunity_id: pickedOpportunityId }, getTenantId()),
    staleTime: 10_000,
    enabled: targetType === "proposal" && Boolean(pickedOpportunityId),
  });

  const deals = dealsQuery.data?.items ?? [];
  const quotes = quotesQuery.data?.items ?? [];
  const proposals = proposalsQuery.data?.items ?? [];
  const canSubmit = Boolean(reviewType && targetType && targetId);

  const createMutation = useMutation({
    mutationFn: () =>
      createReview(getTenantId(), reviewType, targetId, targetType),
    onSuccess: (review: { id?: string }) => {
      void queryClient.invalidateQueries({ queryKey: ["reviews"] });
      if (review?.id) {
        router.push(`/v3/reviews/${review.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New review</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/reviews — required review_type + target_id + target_type query. assigned_to
        defaults to empty. Null body. No assign/decide workflow here.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Review type</span>
          <select
            value={reviewType}
            onChange={(e) => {
              const next = e.target.value as ReviewType | "";
              setReviewType(next);
              const nextTarget = next ? defaultTargetType(next) : "";
              setTargetType(nextTarget);
              setPickedOpportunityId("");
              setPickedTargetId("");
            }}
            required
            className={INPUT_CLASS}
            data-testid="create-review-type"
          >
            <option value="">Select a review type</option>
            {REVIEW_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Target type</span>
          <select
            value={targetType}
            onChange={(e) => {
              setTargetType(e.target.value as TargetType);
              setPickedOpportunityId("");
              setPickedTargetId("");
            }}
            required
            className={INPUT_CLASS}
            data-testid="create-review-target-type"
            disabled={!reviewType}
          >
            <option value="">{reviewType ? "Select a target type" : "Select a review type first"}</option>
            <option value="opportunity">opportunity</option>
            <option value="quote">quote</option>
            <option value="proposal">proposal</option>
          </select>
        </label>
        {targetType ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">
              {targetType === "opportunity" ? "Deal" : "Deal (to load target)"}
            </span>
            <select
              value={pickedOpportunityId}
              onChange={(e) => {
                setPickedOpportunityId(e.target.value);
                setPickedTargetId("");
              }}
              required={targetType === "opportunity" || needsDealFilter}
              className={INPUT_CLASS}
              data-testid="create-review-opportunity"
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
        ) : null}
        {targetType === "quote" ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Quote</span>
            <select
              value={pickedTargetId}
              onChange={(e) => setPickedTargetId(e.target.value)}
              required
              className={INPUT_CLASS}
              data-testid="create-review-quote"
              disabled={!pickedOpportunityId || quotesQuery.isLoading || quotes.length === 0}
            >
              <option value="">
                {!pickedOpportunityId
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
        ) : null}
        {targetType === "proposal" ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Proposal</span>
            <select
              value={pickedTargetId}
              onChange={(e) => setPickedTargetId(e.target.value)}
              required
              className={INPUT_CLASS}
              data-testid="create-review-proposal"
              disabled={!pickedOpportunityId || proposalsQuery.isLoading || proposals.length === 0}
            >
              <option value="">
                {!pickedOpportunityId
                  ? "Select a deal first"
                  : proposalsQuery.isLoading
                    ? "Loading proposals…"
                    : "Select a proposal"}
              </option>
              {proposals.map((proposal) => (
                <option key={proposal.id} value={proposal.id}>
                  {proposalLabel(proposal)}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>
      {targetType && dealsQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load deals. Retry or create a deal in v3 first.
        </p>
      ) : null}
      {targetType && !dealsQuery.isLoading && !dealsQuery.isError && deals.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-review-no-deals">
          No deals in this tenant. POST /api/v1/reviews needs a target_id.{" "}
          <Link
            href="/v3/crm"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create deal
          </Link>
        </p>
      ) : null}
      {targetType === "quote" && pickedOpportunityId && quotesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load quotes for this deal. Retry or create a quote in v3 first.
        </p>
      ) : null}
      {targetType === "quote" &&
      pickedOpportunityId &&
      !quotesQuery.isLoading &&
      !quotesQuery.isError &&
      quotes.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-review-no-quotes">
          No quotes for this deal. GET /quotes without opportunity_id returns [].{" "}
          <Link
            href="/v3/quotes"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create quote
          </Link>
        </p>
      ) : null}
      {targetType === "proposal" && pickedOpportunityId && proposalsQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load proposals for this deal. Retry or create a proposal in v3 first.
        </p>
      ) : null}
      {targetType === "proposal" &&
      pickedOpportunityId &&
      !proposalsQuery.isLoading &&
      !proposalsQuery.isError &&
      proposals.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-review-no-proposals">
          No proposals for this deal. GET /proposals without opportunity_id returns [].{" "}
          <Link
            href="/v3/proposals"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create proposal
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
          data-testid="create-review-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create review"}
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
