import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  getCompany: jest.fn(),
  listOpportunities: jest.fn(),
  getContactsByCompany: jest.fn(),
  getEntityActivities: jest.fn(),
  listTasks: jest.fn(),
  createOpportunity: jest.fn(),
  searchCompanies: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "co-1" }),
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

jest.mock("../intelligence-tab", () => ({
  IntelligenceTab: () => <div>Intelligence stub</div>,
}));

import { getCompany, listOpportunities, listTasks } from "@/lib/api";
import V3Company360Page from "../page";

const mockedCompany = getCompany as jest.MockedFunction<typeof getCompany>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;
const mockedTasks = listTasks as jest.MockedFunction<typeof listTasks>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3Company360Page />
    </QueryClientProvider>
  );
}

describe("V3 company detail opportunities create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedCompany.mockResolvedValue({
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
      branches: [],
      licenses: [],
      contacts: [],
    });
    mockedOpps.mockResolvedValue({ items: [], total: 0 });
    mockedTasks.mockResolvedValue([]);
  });

  it("does not leak a loaded company to legacy /companies/{id}", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Test Co" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
    expect(document.querySelector('a[href="/v3/companies"]')).not.toBeNull();
  });

  it("does not leak empty opportunities to legacy pipeline or CRM-only CTA", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Test Co" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Opportunities" }));
    expect(await screen.findByText("No opportunities for this company")).toBeInTheDocument();
    expect(document.querySelector('a[href="/pipeline"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(screen.queryByRole("link", { name: /open crm/i })).not.toBeInTheDocument();
    expect(screen.getByTestId("company-deals-empty-create")).toBeInTheDocument();
  });

  it("opens the in-v3 create form with locked company_id", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Test Co" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Opportunities" }));
    fireEvent.click(await screen.findByTestId("company-deals-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-deal-submit")).toBeInTheDocument();
    });
    expect(screen.getByTestId("create-deal-company-locked")).toBeInTheDocument();
  });

  it("keeps populated opportunities and tasks tabs off legacy /companies/{id}", async () => {
    mockedOpps.mockResolvedValue({
      items: [
        {
          id: "opp-1",
          name: "Deal A",
          stage: "qualification",
          value: 1000,
          company_id: "co-1",
          status: "open",
        },
      ],
      total: 1,
    });
    mockedTasks.mockResolvedValue([
      {
        id: "task-1",
        title: "Follow up",
        priority: "medium",
        source: "manual",
        company_id: "co-1",
        completed: false,
      },
    ]);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Test Co" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Opportunities" }));
    expect(await screen.findByRole("link", { name: "Deal A" })).toHaveAttribute(
      "href",
      "/v3/crm/opp-1"
    );
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
    fireEvent.click(screen.getByRole("tab", { name: "Tasks" }));
    expect(await screen.findByRole("link", { name: "Follow up" })).toHaveAttribute(
      "href",
      "/v3/tasks/task-1"
    );
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
  });
});
