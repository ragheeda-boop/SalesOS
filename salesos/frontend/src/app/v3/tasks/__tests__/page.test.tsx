import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  listTasks: jest.fn(),
  completeTask: jest.fn(),
  createTask: jest.fn(),
  searchCompanies: jest.fn(),
  listOpportunities: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

import { listTasks, searchCompanies, listOpportunities } from "@/lib/api";
import V3TasksPage from "../page";

const mockedList = listTasks as jest.MockedFunction<typeof listTasks>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3TasksPage />
    </QueryClientProvider>
  );
}

describe("V3TasksPage empty / create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedList.mockResolvedValue([]);
    mockedCompanies.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 });
    mockedOpps.mockResolvedValue({ items: [], total: 0 });
  });

  it("does not leak an empty tenant to a legacy /tasks page", async () => {
    renderPage();
    expect(await screen.findByText("No tasks found")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy tasks/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/tasks"]')).toBeNull();
    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(screen.getByTestId("tasks-empty-create")).toBeInTheDocument();
  });

  it("opens the in-v3 create form from the empty state", async () => {
    renderPage();
    fireEvent.click(await screen.findByTestId("tasks-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-task-submit")).toBeInTheDocument();
    });
  });
});
