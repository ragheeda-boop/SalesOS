import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  listOpportunities: jest.fn(),
}));

jest.mock("@/lib/api/quotes", () => ({
  listQuotes: jest.fn(),
}));

jest.mock("@/lib/api/proposals", () => ({
  listProposals: jest.fn(),
}));

jest.mock("@/lib/api/reviews", () => ({
  createReview: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { listOpportunities } from "@/lib/api";
import { listQuotes } from "@/lib/api/quotes";
import { listProposals } from "@/lib/api/proposals";
import { createReview } from "@/lib/api/reviews";
import { CreateReviewForm } from "../create-review-form";

const mockedCreate = createReview as jest.MockedFunction<typeof createReview>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;
const mockedQuotes = listQuotes as jest.MockedFunction<typeof listQuotes>;
const mockedProposals = listProposals as jest.MockedFunction<typeof listProposals>;

function renderForm(props?: { onCancel?: () => void }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateReviewForm onCancel={props?.onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateReviewForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedOpps.mockResolvedValue({
      items: [
        {
          id: "opp-1",
          name: "Deal A",
          stage: "qualification",
          value: 1000,
          company_id: "co-1",
        },
      ],
      total: 1,
    });
    mockedQuotes.mockResolvedValue({
      items: [
        {
          id: "q-1",
          tenant_id: "tenant-1",
          opportunity_id: "opp-1",
          title: "Quote A",
          status: "DRAFT",
          version: 1,
          lines: [],
          revisions: [],
          approval: { level: "self" },
          currency: "SAR",
          created_at: "2026-09-12T00:00:00Z",
          updated_at: "2026-09-12T00:00:00Z",
          subtotal: 0,
          total_discount: 0,
          total_tax: 0,
          grand_total: 1000,
        },
      ],
      total: 1,
    });
    mockedProposals.mockResolvedValue({
      items: [{ id: "p-1", status: "draft", opportunity_id: "opp-1", title: "Proposal A" }],
      total: 1,
    });
  });

  it("keeps submit disabled until review_type, target_type, and target_id are present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-review-submit");
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "deal_review" },
    });
    expect(screen.getByTestId("create-review-target-type")).toHaveValue("opportunity");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createReview and stays on /v3/reviews/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "rev-new",
      status: "pending",
      review_type: "deal_review",
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "deal_review" },
    });
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-review-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith(
        "tenant-1",
        "deal_review",
        "opp-1",
        "opportunity"
      );
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/reviews/rev-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/reviews");
    expect(mockPush).not.toHaveBeenCalledWith("/opportunities");
  });

  it("maps quote_review to quote target and posts quote_id", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "rev-q",
      status: "pending",
      review_type: "quote_review",
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "quote_review" },
    });
    expect(screen.getByTestId("create-review-target-type")).toHaveValue("quote");
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    await screen.findByRole("option", { name: "q-1 · DRAFT · v1" });
    fireEvent.change(screen.getByTestId("create-review-quote"), {
      target: { value: "q-1" },
    });
    fireEvent.click(screen.getByTestId("create-review-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "quote_review", "q-1", "quote");
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/reviews/rev-q");
    });
  });

  it("shows an honest API error and does not invent a review", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "deal_review" },
    });
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-review-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create reviews."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/crm when no opportunity_id options exist", async () => {
    mockedOpps.mockResolvedValueOnce({ items: [], total: 0 });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "deal_review" },
    });
    expect(await screen.findByTestId("create-review-no-deals")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create deal/i })).toHaveAttribute("href", "/v3/crm");
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/reviews"]')).toBeNull();
    expect(screen.getByTestId("create-review-submit")).toBeDisabled();
  });

  it("points to /v3/quotes when quote_review has no quote_id", async () => {
    mockedQuotes.mockResolvedValue({ items: [], total: 0 });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "quote_review" },
    });
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(await screen.findByTestId("create-review-no-quotes")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create quote/i })).toHaveAttribute(
      "href",
      "/v3/quotes"
    );
    expect(document.querySelector('a[href="/quotes"]')).toBeNull();
    expect(screen.getByTestId("create-review-submit")).toBeDisabled();
  });

  it("points to /v3/proposals when proposal_review has no proposal_id", async () => {
    mockedProposals.mockResolvedValue({ items: [], total: 0 });
    renderForm();
    fireEvent.change(screen.getByTestId("create-review-type"), {
      target: { value: "proposal_review" },
    });
    expect(screen.getByTestId("create-review-target-type")).toHaveValue("proposal");
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-review-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(await screen.findByTestId("create-review-no-proposals")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create proposal/i })).toHaveAttribute(
      "href",
      "/v3/proposals"
    );
    expect(document.querySelector('a[href="/proposals"]')).toBeNull();
    expect(screen.getByTestId("create-review-submit")).toBeDisabled();
  });
});
