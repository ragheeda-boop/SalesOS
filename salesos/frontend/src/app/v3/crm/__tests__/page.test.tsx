import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  listOpportunities: jest.fn(),
  createOpportunity: jest.fn(),
  searchCompanies: jest.fn(),
  advanceOpportunity: jest.fn(),
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

import { listOpportunities, searchCompanies } from "@/lib/api";
import V3CrmPage from "../page";

const mockedList = listOpportunities as jest.MockedFunction<typeof listOpportunities>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3CrmPage />
    </QueryClientProvider>
  );
}

describe("V3CrmPage empty / create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedList.mockResolvedValue({ items: [], total: 0 });
    mockedCompanies.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 });
  });

  it("does not leak an empty tenant to legacy /pipeline or /opportunities", async () => {
    renderPage();
    expect(await screen.findByText("No deals yet")).toBeInTheDocument();
    expect(document.querySelector('a[href="/pipeline"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(screen.getByTestId("crm-empty-create")).toBeInTheDocument();
  });

  it("opens the in-v3 create form from the empty state", async () => {
    renderPage();
    fireEvent.click(await screen.findByTestId("crm-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-deal-submit")).toBeInTheDocument();
    });
  });
});
