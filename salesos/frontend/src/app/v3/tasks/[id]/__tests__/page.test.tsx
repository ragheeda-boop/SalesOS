import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  listTasks: jest.fn(),
  getCompany: jest.fn(),
  completeTask: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "task-1" }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

import { listTasks, getCompany } from "@/lib/api";
import V3TaskDetailPage from "../page";

const mockedList = listTasks as jest.MockedFunction<typeof listTasks>;
const mockedCompany = getCompany as jest.MockedFunction<typeof getCompany>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3TaskDetailPage />
    </QueryClientProvider>
  );
}

describe("V3 task detail /companies leak", () => {
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
  });

  it("does not leak a linked company to legacy /companies/{id}", async () => {
    mockedList.mockResolvedValue([
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
    expect(await screen.findByRole("heading", { name: "Follow up" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Open Company 360" })).toHaveAttribute(
      "href",
      "/v3/companies/co-1"
    );
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
    expect(document.querySelector('a[href="/v3/tasks"]')).not.toBeNull();
  });

  it("keeps the no-company empty state inside v3", async () => {
    mockedList.mockResolvedValue([
      {
        id: "task-1",
        title: "Unlinked task",
        priority: "medium",
        source: "manual",
        company_id: null,
        completed: false,
      },
    ]);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Unlinked task" })).toBeInTheDocument();
    expect(await screen.findByText("No company linked")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
    expect(screen.getByRole("link", { name: "Browse companies" })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
  });
});
