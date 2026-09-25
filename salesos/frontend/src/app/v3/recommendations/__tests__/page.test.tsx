import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getRecommendations } from "@/lib/api";
import V3RecommendationsPage from "../page";

jest.mock("@/lib/api", () => ({ getRecommendations: jest.fn() }));
jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));
jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true }),
}));

const recommendationsMock = getRecommendations as jest.MockedFunction<typeof getRecommendations>;

describe("V3RecommendationsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows rule-based recommendations, source evidence, and a deal review link", async () => {
    recommendationsMock.mockResolvedValue({
      items: [{
        id: "rec-1",
        title: "Escalate: Stalled deal at critical risk",
        description: "Deal health is 20% (critical). Escalate to management.",
        reasoning: "Health score 20% below 40%",
        priority: "critical",
        confidence: 0.3,
        target_id: "opp-1",
        target_type: "opportunity",
        evidence: [{
          source_domain: "deal_intelligence",
          source_type: "risk_factor",
          description: "Stalled 46 days in proposal",
          confidence: 0.8,
        }],
      }],
      total: 1,
      source_opportunities: 1,
      skipped_missing_probability: 0,
      generated_at: "2026-09-21T08:00:00Z",
      method: "deterministic_crm_rules",
      mutated_crm: false,
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={client}>
        <V3RecommendationsPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Escalate: Stalled deal at critical risk")).toBeInTheDocument();
    expect(screen.getByText("Stalled 46 days in proposal", { exact: false })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review deal" })).toHaveAttribute("href", "/v3/crm/opp-1");
    expect(screen.getByText(/do not change CRM records or send communications/i)).toBeInTheDocument();
  });
});
