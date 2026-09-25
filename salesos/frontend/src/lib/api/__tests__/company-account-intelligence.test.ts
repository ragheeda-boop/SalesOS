import api from "../client";
import { getCompanyAccountIntelligence, recordCompanyAccountEvidence } from "../company";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("getCompanyAccountIntelligence", () => {
  beforeEach(() => jest.clearAllMocks());

  it("loads the encoded company id with explicit tenant context", async () => {
    const response = {
      company_id: "co/1",
      company_name: "Test Co",
      industry: null,
      city: null,
      company_status: "active",
      total_opportunities: 0,
      active_opportunities: 0,
      won_deals: 0,
      lost_deals: 0,
      activity_count: 0,
      last_activity_at: null,
      days_since_activity: null,
      missing_data: ["opportunity_history", "activity_history"],
      account_signals: {
        status: "insufficient_data" as const,
        signals: [
          {
            code: "NO_OPPORTUNITY_HISTORY",
            polarity: "neutral" as const,
            title: "No opportunity history",
            detail: "No opportunities are linked to this account in the tenant CRM.",
            source: "commercial_opportunities",
          },
          {
            code: "NO_ACTIVITY_HISTORY",
            polarity: "neutral" as const,
            title: "No activity recorded",
            detail: "No company activity is recorded in the tenant CRM.",
            source: "activity_records",
          },
        ],
        recommendations: [],
      },
      engagement_trend: {
        trend: "insufficient_data" as const,
        recent_90_days: 0,
        previous_90_days: 0,
        change_percent: null,
        method: "activity_count_90d_comparison_v1" as const,
        interpretation: "Activity volume only; it does not measure customer sentiment or deal quality.",
      },
      generated_at: "2026-09-21T10:00:00+00:00",
      method: "persisted_crm_records_with_explainable_rules" as const,
      mutated_crm: false as const,
    };
    mockApi.get.mockResolvedValueOnce({ data: response });

    await expect(getCompanyAccountIntelligence("co/1", "tenant-1")).resolves.toEqual(response);
    expect(mockApi.get).toHaveBeenCalledWith(
      "/api/v1/companies/co%2F1/account-intelligence",
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });

  it("records an idempotent evidence snapshot through the tenant API", async () => {
    const response = {
      insight_id: "insight-1",
      created: true,
      evidence_count: 2,
      overall_confidence: 0.55,
      confidence_level: "medium",
      idempotency_key: "account-signals-v1:hash",
    };
    mockApi.post.mockResolvedValueOnce({ data: response });

    await expect(recordCompanyAccountEvidence("co/1", "tenant-1")).resolves.toEqual(response);
    expect(mockApi.post).toHaveBeenCalledWith(
      "/api/v1/companies/co%2F1/account-intelligence/evidence",
      {},
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });
});
