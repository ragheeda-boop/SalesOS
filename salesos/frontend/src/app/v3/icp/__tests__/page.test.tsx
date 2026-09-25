import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import apiClient from "@/lib/api/client";
import V3ICPPage from "../page";

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));
jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true }),
}));

const api = apiClient as jest.Mocked<typeof apiClient>;

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <V3ICPPage />
    </QueryClientProvider>
  );
}

describe("V3 ICP scoring", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.get.mockResolvedValue({
      data: {
        profiles: [
          {
            id: "profile-1",
            name: "Saudi technology buyers",
            description: "",
            is_active: true,
            schema_version: 2,
            criteria: { industries: ["technology"], cities: ["riyadh"] },
          },
        ],
        count: 1,
      },
    } as never);
  });

  it("scores entered company fields against the tenant's persisted ICP profile", async () => {
    api.post.mockResolvedValueOnce({
      data: {
        profile_id: "profile-1",
        schema_version: 2,
        score: 3,
        max_score: 3,
        fit_ratio: 1,
        matched: { industry: true, city: true },
        company: { industry: "technology", city: "riyadh" },
      },
    } as never);
    renderPage();

    fireEvent.change(await screen.findByLabelText("Company name"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Company industry"), { target: { value: "Technology" } });
    fireEvent.change(screen.getByLabelText("Company city"), { target: { value: "Riyadh" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate profile fit" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/api/v1/icp/profiles/profile-1/score",
        expect.objectContaining({ name: "Acme", industry: "Technology", city: "Riyadh" }),
        { headers: { "X-Tenant-Id": "tenant-1" } }
      );
    });
    expect(await screen.findByText(/Fit: 100% · 3 \/ 3 points/)).toBeInTheDocument();
    expect(screen.getByText("industry: match")).toBeInTheDocument();
  });
});
