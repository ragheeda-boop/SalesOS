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
  createProposal: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { listOpportunities } from "@/lib/api";
import { listQuotes } from "@/lib/api/quotes";
import { createProposal } from "@/lib/api/proposals";
import { CreateProposalForm } from "../create-proposal-form";

const mockedCreate = createProposal as jest.MockedFunction<typeof createProposal>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;
const mockedQuotes = listQuotes as jest.MockedFunction<typeof listQuotes>;

function renderForm(props?: { opportunityId?: string; onCancel?: () => void }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateProposalForm opportunityId={props?.opportunityId} onCancel={props?.onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateProposalForm", () => {
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
  });

  it("keeps submit disabled until opportunity_id and quote_id are present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-proposal-submit");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-proposal-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "q-1 · DRAFT · v1" });
    fireEvent.change(screen.getByTestId("create-proposal-quote"), {
      target: { value: "q-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createProposal and stays on /v3/proposals/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "p-new",
      status: "draft",
      sections: 4,
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-proposal-opportunity"), {
      target: { value: "opp-1" },
    });
    await screen.findByRole("option", { name: "q-1 · DRAFT · v1" });
    fireEvent.change(screen.getByTestId("create-proposal-quote"), {
      target: { value: "q-1" },
    });
    fireEvent.click(screen.getByTestId("create-proposal-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "opp-1", "q-1");
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/proposals/p-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/opportunities");
    expect(mockPush).not.toHaveBeenCalledWith("/proposals");
  });

  it("locks opportunity_id when provided and does not fetch a deal picker", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "p-locked",
      status: "draft",
      sections: 4,
    });
    renderForm({ opportunityId: "opp-locked" });
    expect(screen.getByTestId("create-proposal-opportunity-locked")).toBeInTheDocument();
    expect(screen.queryByTestId("create-proposal-opportunity")).not.toBeInTheDocument();
    await screen.findByRole("option", { name: "q-1 · DRAFT · v1" });
    fireEvent.change(screen.getByTestId("create-proposal-quote"), {
      target: { value: "q-1" },
    });
    fireEvent.click(screen.getByTestId("create-proposal-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "opp-locked", "q-1");
    });
    expect(mockedOpps).not.toHaveBeenCalled();
    expect(mockedQuotes).toHaveBeenCalledWith(
      { opportunity_id: "opp-locked" },
      "tenant-1"
    );
  });

  it("shows an honest API error and does not invent a proposal", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-proposal-opportunity"), {
      target: { value: "opp-1" },
    });
    await screen.findByRole("option", { name: "q-1 · DRAFT · v1" });
    fireEvent.change(screen.getByTestId("create-proposal-quote"), {
      target: { value: "q-1" },
    });
    fireEvent.click(screen.getByTestId("create-proposal-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create proposals."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/crm when no opportunity_id options exist", async () => {
    mockedOpps.mockResolvedValueOnce({ items: [], total: 0 });
    renderForm();
    expect(await screen.findByTestId("create-proposal-no-deals")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create deal/i })).toHaveAttribute("href", "/v3/crm");
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/proposals"]')).toBeNull();
    expect(screen.getByTestId("create-proposal-submit")).toBeDisabled();
  });

  it("points to /v3/quotes when the selected deal has no quote_id", async () => {
    mockedQuotes.mockResolvedValue({ items: [], total: 0 });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-proposal-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(await screen.findByTestId("create-proposal-no-quotes")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create quote/i })).toHaveAttribute(
      "href",
      "/v3/quotes"
    );
    expect(document.querySelector('a[href="/quotes"]')).toBeNull();
    expect(screen.getByTestId("create-proposal-submit")).toBeDisabled();
  });
});
