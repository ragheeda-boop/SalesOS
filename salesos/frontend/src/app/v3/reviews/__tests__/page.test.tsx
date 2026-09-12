import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

jest.mock("@/lib/api", () => ({
  listOpportunities: jest.fn(),
}));

jest.mock("@/lib/api/quotes", () => ({
  listQuotes: jest.fn(),
}));

jest.mock("@/lib/api/proposals", () => ({
  listProposals: jest.fn(),
}));

jest.mock("@/lib/api/reviews", () => ({
  createReview: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

import apiClient from "@/lib/api/client";
import { listOpportunities } from "@/lib/api";
import V3ReviewsPage from "../page";

const mockedGet = apiClient.get as jest.MockedFunction<typeof apiClient.get>;
const mockedOpps = listOpportunities as jest.MockedFunction<typeof listOpportunities>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3ReviewsPage />
    </QueryClientProvider>
  );
}

describe("V3ReviewsPage empty / create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGet.mockResolvedValue({ data: { items: [], total: 0 } } as never);
    mockedOpps.mockResolvedValue({ items: [], total: 0 });
  });

  it("does not leak an empty tenant to legacy hubs", async () => {
    renderPage();
    expect(await screen.findByText("No reviews yet")).toBeInTheDocument();
    expect(document.querySelector('a[href="/reviews"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/quotes"]')).toBeNull();
    expect(document.querySelector('a[href="/proposals"]')).toBeNull();
    expect(screen.getByTestId("reviews-empty-create")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Browse deals" })).toHaveAttribute("href", "/v3/crm");
  });

  it("opens the in-v3 create form from the empty state", async () => {
    renderPage();
    fireEvent.click(await screen.findByTestId("reviews-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-review-submit")).toBeInTheDocument();
    });
  });
});
