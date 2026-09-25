import api from "../client";
import {
  createPipeline,
  getDealIntelligence,
  getOpportunityNBA,
  getRecommendations,
  getPipelineAnalyticsSummary,
  refreshOpportunityNBA,
} from "../pipeline";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createPipeline — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/pipelines with a null body and tenant header", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        id: "pipe-tenant-1",
        name: "Sales Pipeline",
        stages: ["prospecting", "qualification"],
      },
    });

    const result = await createPipeline("tenant-1");

    expect(result.id).toBe("pipe-tenant-1");
    expect(result.name).toBe("Sales Pipeline");
    expect(Array.isArray(result.stages)).toBe(true);
    expect(mockApi.post).toHaveBeenCalledWith("/api/v1/pipelines", null, {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});

describe("getPipelineAnalyticsSummary — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("reads persisted tenant pipeline metrics from the analytics route", async () => {
    const summary = {
      velocity: { qualification: { avg_days: 12.5, entries: 4 } },
      conversion_rates: { "qualification→proposal": 0.5 },
      health_map: { healthy: 1, at_risk: 2, critical: 0, opportunities: [] },
      forecast: {
        currency: "SAR",
        best_case: 1000,
        commit: 600,
        pipeline: 1000,
        gap: 400,
        avg_probability: 0.6,
        total_deals: 3,
        by_currency: [
          {
            currency: "SAR",
            best_case: 1000,
            commit: 600,
            pipeline: 1000,
            gap: 400,
            avg_probability: 0.6,
            total_deals: 3,
          },
        ],
      },
      total_open_deals: 3,
    };
    mockApi.get.mockResolvedValueOnce({ data: summary });

    await expect(getPipelineAnalyticsSummary("tenant-1")).resolves.toEqual(summary);
    expect(mockApi.get).toHaveBeenCalledWith("/api/v1/pipeline/summary", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});

describe("opportunity NBA — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads an opportunity-scoped recommendation with tenant context", async () => {
    mockApi.get.mockResolvedValueOnce({ data: { id: "nba-1", action: "call" } });

    await expect(getOpportunityNBA("opp/1", "tenant-1")).resolves.toMatchObject({
      id: "nba-1",
      action: "call",
    });
    expect(mockApi.get).toHaveBeenCalledWith("/api/v1/opportunities/opp%2F1/nba", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });

  it("refreshes through the supported POST contract", async () => {
    mockApi.post.mockResolvedValueOnce({ data: { id: "nba-2", action: "follow_up" } });

    await expect(refreshOpportunityNBA("opp-1", "tenant-1")).resolves.toMatchObject({
      id: "nba-2",
    });
    expect(mockApi.post).toHaveBeenCalledWith(
      "/api/v1/opportunities/opp-1/nba/refresh",
      null,
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });
});

describe("getDealIntelligence — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("requests tenant-scoped intelligence for the selected opportunity", async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { deal_id: "opp-1", health_level: "unknown", missing_fields: ["probability"] },
    });

    await expect(getDealIntelligence("opp 1", "tenant-1")).resolves.toMatchObject({
      deal_id: "opp-1",
      health_level: "unknown",
    });
    expect(mockApi.get).toHaveBeenCalledWith(
      "/api/v1/opportunities/opp%201/intelligence",
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });
});

describe("getRecommendations — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads the tenant-scoped recommendation list", async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { items: [], total: 0, mutated_crm: false },
    });

    await expect(getRecommendations("tenant-1")).resolves.toMatchObject({
      items: [],
      mutated_crm: false,
    });
    expect(mockApi.get).toHaveBeenCalledWith("/api/v1/recommendations", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
