import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  getGlobalActivities: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("@/lib/hooks/useActivityIntelligence", () => ({
  useActivityIntelligence: () => ({
    dashboard: { data: null, isLoading: false, error: null },
  }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

import { getGlobalActivities } from "@/lib/api";
import V3ActivitiesPage from "../page";

const mockedActivities = getGlobalActivities as jest.MockedFunction<typeof getGlobalActivities>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3ActivitiesPage />
    </QueryClientProvider>
  );
}

describe("V3 activities /activities leak", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("does not leak the activities header to legacy /activities", async () => {
    mockedActivities.mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Activities" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy activities/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/activities"]')).toBeNull();
  });

  it("keeps a populated feed inside v3", async () => {
    mockedActivities.mockResolvedValue({
      items: [
        {
          id: "act-1",
          tenant_id: "tenant-1",
          actor: "Ada",
          action: "email",
          entity_type: "company",
          entity_id: "co-1",
          timestamp: "2026-09-12T00:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Activities" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy activities/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/activities"]')).toBeNull();
  });
});
