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
  createQuote: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { listOpportunities } from "@/lib/api";
import { createQuote } from "@/lib/api/quotes";
import { CreateQuoteForm } from "../create-quote-form";

const mockedCreate = createQuote as jest.MockedFunction<typeof createQuote>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;

function renderForm(props?: { opportunityId?: string; onCancel?: () => void }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateQuoteForm opportunityId={props?.opportunityId} onCancel={props?.onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateQuoteForm", () => {
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
  });

  it("keeps submit disabled until title and opportunity_id are present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-quote-submit");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-quote-title"), {
      target: { value: "عرض سعر" },
    });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-quote-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createQuote and stays on /v3/quotes/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "q-new",
      title: "عرض سعر",
      status: "DRAFT",
      version: 1,
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-quote-title"), {
      target: { value: "عرض سعر" },
    });
    fireEvent.change(screen.getByTestId("create-quote-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-quote-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "opp-1", "عرض سعر");
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/quotes/q-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/opportunities");
    expect(mockPush).not.toHaveBeenCalledWith("/quotes");
  });

  it("locks opportunity_id when provided and does not fetch a picker", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "q-locked",
      title: "Locked quote",
      status: "DRAFT",
      version: 1,
    });
    renderForm({ opportunityId: "opp-locked" });
    expect(screen.getByTestId("create-quote-opportunity-locked")).toBeInTheDocument();
    expect(screen.queryByTestId("create-quote-opportunity")).not.toBeInTheDocument();
    fireEvent.change(screen.getByTestId("create-quote-title"), {
      target: { value: "Locked quote" },
    });
    fireEvent.click(screen.getByTestId("create-quote-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "opp-locked", "Locked quote");
    });
    expect(mockedOpps).not.toHaveBeenCalled();
  });

  it("shows an honest API error and does not invent a quote", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-quote-title"), {
      target: { value: "عرض" },
    });
    fireEvent.change(screen.getByTestId("create-quote-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-quote-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create quotes."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/crm when no opportunity_id options exist", async () => {
    mockedOpps.mockResolvedValueOnce({ items: [], total: 0 });
    renderForm();
    expect(await screen.findByTestId("create-quote-no-deals")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create deal/i })).toHaveAttribute("href", "/v3/crm");
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/quotes"]')).toBeNull();
    expect(screen.getByTestId("create-quote-submit")).toBeDisabled();
  });
});
