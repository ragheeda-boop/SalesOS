import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getDealIntelligence } from "@/lib/api";
import { DealIntelligenceTab } from "../intelligence-tab";

jest.mock("@/lib/api", () => ({ getDealIntelligence: jest.fn() }));
jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));

const getIntelligenceMock = getDealIntelligence as jest.MockedFunction<typeof getDealIntelligence>;

describe("DealIntelligenceTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders CRM-derived risk inputs and the calculation boundary", async () => {
    getIntelligenceMock.mockResolvedValue({
      deal_id: "opp-1",
      deal_name: "ERP Upgrade",
      health_score: 0.82,
      health_level: "healthy",
      risk_factors: [],
      opportunity_factors: ["High probability (72%)", "High value deal (120,000)"],
      stage: "proposal",
      value: 120000,
      probability: 0.72,
      days_in_stage: 8,
      activity_count: 6,
      missing_fields: [],
      generated_at: "2026-09-21T08:00:00Z",
      method: "deterministic_crm_rules",
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={client}>
        <DealIntelligenceTab opportunityId="opp-1" />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Healthy · 82%")).toBeInTheDocument();
    expect(screen.getByText("High probability (72%)")).toBeInTheDocument();
    expect(screen.getByText(/not a calibrated sales prediction/i)).toBeInTheDocument();
  });

  it("shows missing data rather than a made-up health score", async () => {
    getIntelligenceMock.mockResolvedValue({
      deal_id: "opp-2",
      deal_name: "Unscored",
      health_score: null,
      health_level: "unknown",
      risk_factors: ["Probability is missing; health score was not calculated."],
      opportunity_factors: [],
      stage: "qualification",
      value: 50000,
      probability: null,
      days_in_stage: null,
      activity_count: 0,
      missing_fields: ["probability", "days_in_stage"],
      generated_at: "2026-09-21T08:00:00Z",
      method: "deterministic_crm_rules",
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={client}>
        <DealIntelligenceTab opportunityId="opp-2" />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Insufficient CRM data")).toBeInTheDocument();
    expect(screen.getByText(/probability, days in stage/i)).toBeInTheDocument();
  });
});
