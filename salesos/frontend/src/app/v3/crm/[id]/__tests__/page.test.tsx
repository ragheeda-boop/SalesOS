import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  getOpportunity: jest.fn(),
  listOpportunities: jest.fn(),
  getCompany: jest.fn(),
  getEntityActivities: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "opp-1" }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

import { getOpportunity, listOpportunities } from "@/lib/api";
import V3Deal360Page from "../page";

const mockedGet = getOpportunity as jest.MockedFunction<typeof getOpportunity>;
const mockedList = listOpportunities as jest.MockedFunction<typeof listOpportunities>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3Deal360Page />
    </QueryClientProvider>
  );
}

describe("V3 deal 360 /opportunities leak", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedList.mockResolvedValue({ items: [], total: 0 });
  });

  it("does not leak a loaded deal to legacy /opportunities", async () => {
    mockedGet.mockResolvedValue({
      id: "opp-1",
      name: "Deal A",
      stage: "qualification",
      value: 1000,
      company_id: "co-1",
      company_name: "Test Co",
      status: "open",
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Deal A" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy opportunities/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(screen.getByRole("link", { name: "Back to CRM" })).toHaveAttribute("href", "/v3/crm");
    expect(screen.getByRole("link", { name: "Company 360" })).toHaveAttribute(
      "href",
      "/v3/companies/co-1"
    );
  });

  it("keeps a deal without company_id inside v3", async () => {
    mockedGet.mockResolvedValue({
      id: "opp-1",
      name: "Unlinked deal",
      stage: "qualification",
      value: 0,
      company_id: "",
      status: "open",
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Unlinked deal" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy opportunities/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(screen.getByRole("link", { name: "Back to CRM" })).toHaveAttribute("href", "/v3/crm");
    fireEvent.click(screen.getByRole("tab", { name: "Contacts" }));
    expect(await screen.findByText("No company linked")).toBeInTheDocument();
    const crmLinks = screen.getAllByRole("link", { name: "Back to CRM" });
    expect(crmLinks.length).toBeGreaterThanOrEqual(1);
    crmLinks.forEach((link) => expect(link).toHaveAttribute("href", "/v3/crm"));
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
  });
});
