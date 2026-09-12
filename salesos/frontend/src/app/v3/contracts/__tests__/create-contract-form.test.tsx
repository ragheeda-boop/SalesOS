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

jest.mock("@/lib/api/contracts", () => ({
  createContract: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { listOpportunities } from "@/lib/api";
import { listQuotes } from "@/lib/api/quotes";
import { createContract } from "@/lib/api/contracts";
import { CreateContractForm } from "../create-contract-form";

const mockedCreate = createContract as jest.MockedFunction<typeof createContract>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;
const mockedQuotes = listQuotes as jest.MockedFunction<typeof listQuotes>;

function renderForm(props?: { onCancel?: () => void }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateContractForm onCancel={props?.onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateContractForm", () => {
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
          status: "APPROVED",
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

  it("keeps submit disabled until opportunity_id is present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-contract-submit");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-contract-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createContract with opportunity_id only and stays on /v3/contracts/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "c-new",
      tenant_id: "tenant-1",
      opportunity_id: "opp-1",
      title: "",
      status: "DRAFT",
      parties: [],
      obligations: [],
      renewal: { auto_renew: false, notice_days: 0, renewal_term_months: 0, max_renewals: 0 },
      created_at: "2026-09-12T00:00:00Z",
      updated_at: "2026-09-12T00:00:00Z",
      version: 1,
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-contract-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-contract-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith({ opportunity_id: "opp-1" }, "tenant-1");
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/contracts/c-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/opportunities");
    expect(mockPush).not.toHaveBeenCalledWith("/contracts");
  });

  it("includes optional quote_id and title when set", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "c-quoted",
      tenant_id: "tenant-1",
      opportunity_id: "opp-1",
      quote_id: "q-1",
      title: "MSA",
      status: "DRAFT",
      parties: [],
      obligations: [],
      renewal: { auto_renew: false, notice_days: 0, renewal_term_months: 0, max_renewals: 0 },
      created_at: "2026-09-12T00:00:00Z",
      updated_at: "2026-09-12T00:00:00Z",
      version: 1,
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-contract-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.change(screen.getByTestId("create-contract-title"), {
      target: { value: "MSA" },
    });
    await screen.findByRole("option", { name: "Quote A · APPROVED · v1" });
    fireEvent.change(screen.getByTestId("create-contract-quote"), {
      target: { value: "q-1" },
    });
    fireEvent.click(screen.getByTestId("create-contract-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith(
        { opportunity_id: "opp-1", quote_id: "q-1", title: "MSA" },
        "tenant-1"
      );
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/contracts/c-quoted");
    });
  });

  it("shows an honest API error and does not invent a contract", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-contract-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.click(screen.getByTestId("create-contract-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create contracts."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/crm when no opportunity_id options exist", async () => {
    mockedOpps.mockResolvedValueOnce({ items: [], total: 0 });
    renderForm();
    expect(await screen.findByTestId("create-contract-no-deals")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create deal/i })).toHaveAttribute("href", "/v3/crm");
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/contracts"]')).toBeNull();
    expect(screen.getByTestId("create-contract-submit")).toBeDisabled();
  });

  it("keeps submit enabled when the selected deal has no quote_id", async () => {
    mockedQuotes.mockResolvedValue({ items: [], total: 0 });
    renderForm();
    await screen.findByRole("option", { name: "Deal A" });
    fireEvent.change(screen.getByTestId("create-contract-opportunity"), {
      target: { value: "opp-1" },
    });
    expect(await screen.findByTestId("create-contract-no-quotes")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create quote/i })).toHaveAttribute(
      "href",
      "/v3/quotes"
    );
    expect(document.querySelector('a[href="/quotes"]')).toBeNull();
    expect(screen.getByTestId("create-contract-submit")).not.toBeDisabled();
  });
});
