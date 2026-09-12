import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@salesos/hooks", () => ({
  useDebounce: (value: string) => value,
}));

jest.mock("@/lib/api", () => ({
  searchCompanies: jest.fn(),
  createCompany: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

import { searchCompanies } from "@/lib/api";
import V3CompaniesPage from "../page";

const mockedSearch = searchCompanies as jest.MockedFunction<typeof searchCompanies>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3CompaniesPage />
    </QueryClientProvider>
  );
}

describe("V3CompaniesPage empty / create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedSearch.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 });
  });

  it("does not leak an empty tenant to legacy /companies", async () => {
    renderPage();
    expect(await screen.findByText("No companies found")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy companies/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /\/companies/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(screen.getByTestId("companies-empty-create")).toBeInTheDocument();
  });

  it("opens the in-v3 create form from the empty state", async () => {
    renderPage();
    fireEvent.click(await screen.findByTestId("companies-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-company-submit")).toBeInTheDocument();
    });
  });
});
