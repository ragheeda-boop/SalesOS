import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  createOpportunity: jest.fn(),
  searchCompanies: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { createOpportunity, searchCompanies } from "@/lib/api";
import { CreateDealForm } from "../create-deal-form";

const mockedCreate = createOpportunity as jest.MockedFunction<typeof createOpportunity>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;

function renderForm(props?: { companyId?: string; onCancel?: () => void }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateDealForm companyId={props?.companyId} onCancel={props?.onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateDealForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedCompanies.mockResolvedValue({
      items: [
        {
          id: "co-1",
          name_ar: "شركة اختبار",
          name_en: "Test Co",
          cr_number: "1010000000",
          status: "active",
          created_at: "2026-09-12",
          updated_at: "2026-09-12",
          city: null,
          region: null,
          phone: null,
          email: null,
          confidence_score: null,
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    });
  });

  it("keeps submit disabled until name and company_id are present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-deal-submit");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-deal-name"), {
      target: { value: "صفقة جديدة" },
    });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-deal-company"), {
      target: { value: "co-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createOpportunity and stays on /v3/crm/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "opp-new",
      name: "صفقة جديدة",
      stage: "qualification",
      value: 100000,
      owner_id: "",
    });
    renderForm();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-deal-name"), {
      target: { value: "صفقة جديدة" },
    });
    fireEvent.change(screen.getByTestId("create-deal-company"), {
      target: { value: "co-1" },
    });
    fireEvent.change(screen.getByTestId("create-deal-value"), {
      target: { value: "100000" },
    });
    fireEvent.click(screen.getByTestId("create-deal-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "co-1", "صفقة جديدة", 100000);
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/crm/opp-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/opportunities");
    expect(mockPush).not.toHaveBeenCalledWith("/pipeline");
  });

  it("locks company_id when provided and does not fetch a picker", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "opp-locked",
      name: "Locked deal",
      stage: "qualification",
      value: 0,
      owner_id: "",
    });
    renderForm({ companyId: "co-locked" });
    expect(screen.getByTestId("create-deal-company-locked")).toBeInTheDocument();
    expect(screen.queryByTestId("create-deal-company")).not.toBeInTheDocument();
    fireEvent.change(screen.getByTestId("create-deal-name"), {
      target: { value: "Locked deal" },
    });
    fireEvent.click(screen.getByTestId("create-deal-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1", "co-locked", "Locked deal", 0);
    });
    expect(mockedCompanies).not.toHaveBeenCalled();
  });

  it("shows an honest API error and does not invent a deal", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-deal-name"), {
      target: { value: "صفقة" },
    });
    fireEvent.change(screen.getByTestId("create-deal-company"), {
      target: { value: "co-1" },
    });
    fireEvent.click(screen.getByTestId("create-deal-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create opportunities."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/companies when no company_id options exist", async () => {
    mockedCompanies.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });
    renderForm();
    expect(await screen.findByTestId("create-deal-no-companies")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create company/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
    expect(document.querySelector('a[href="/pipeline"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(screen.getByTestId("create-deal-submit")).toBeDisabled();
  });
});
