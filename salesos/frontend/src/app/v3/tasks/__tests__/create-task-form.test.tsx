import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  createTask: jest.fn(),
  searchCompanies: jest.fn(),
  listOpportunities: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { createTask, searchCompanies, listOpportunities } from "@/lib/api";
import { CreateTaskForm } from "../create-task-form";

const mockedCreate = createTask as jest.MockedFunction<typeof createTask>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;

function renderForm(onCancel?: () => void) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateTaskForm onCancel={onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateTaskForm", () => {
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
    mockedOpps.mockResolvedValue({
      items: [
        {
          id: "opp-1",
          name: "صفقة اختبار",
          stage: "qualification",
          value: 0,
          company_id: "co-1",
        },
      ],
      total: 1,
    });
  });

  it("keeps submit disabled until title is present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-task-submit");
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-task-title"), {
      target: { value: "متابعة عرض" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts createTask and stays on /v3/tasks/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "t-new",
      title: "متابعة عرض",
      priority: "high",
      source: "manual",
      company_id: "co-1",
      opportunity_id: "opp-1",
      completed: false,
      created_at: "2026-09-12",
    });
    renderForm();
    await screen.findByRole("option", { name: "Test Co" });
    await screen.findByRole("option", { name: "صفقة اختبار" });
    fireEvent.change(screen.getByTestId("create-task-title"), {
      target: { value: "متابعة عرض" },
    });
    fireEvent.change(screen.getByTestId("create-task-priority"), {
      target: { value: "high" },
    });
    fireEvent.change(screen.getByTestId("create-task-company"), {
      target: { value: "co-1" },
    });
    fireEvent.change(screen.getByTestId("create-task-opportunity"), {
      target: { value: "opp-1" },
    });
    fireEvent.change(screen.getByTestId("create-task-due-date"), {
      target: { value: "2026-09-20" },
    });
    fireEvent.click(screen.getByTestId("create-task-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith(
        "tenant-1",
        "متابعة عرض",
        "high",
        "co-1",
        "manual",
        "opp-1",
        "2026-09-20"
      );
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/tasks/t-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/tasks");
  });

  it("shows an honest API error and does not invent a task", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-task-title"), {
      target: { value: "متابعة" },
    });
    fireEvent.click(screen.getByTestId("create-task-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create tasks."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("allows create without company_id and points empty picker to /v3/companies", async () => {
    mockedCompanies.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });
    mockedOpps.mockResolvedValueOnce({ items: [], total: 0 });
    renderForm();
    expect(await screen.findByTestId("create-task-no-companies")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create company/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
    expect(document.querySelector('a[href="/tasks"]')).toBeNull();
    fireEvent.change(screen.getByTestId("create-task-title"), {
      target: { value: "مهمة بلا شركة" },
    });
    expect(screen.getByTestId("create-task-submit")).not.toBeDisabled();
  });
});
