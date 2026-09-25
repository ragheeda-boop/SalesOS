import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "@salesos/ui";

jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));
jest.mock("@/lib/api", () => ({
  getCompanyAccountIntelligence: jest.fn(),
  recordCompanyAccountEvidence: jest.fn(),
}));

import { getCompanyAccountIntelligence, recordCompanyAccountEvidence } from "@/lib/api";
import { IntelligenceTab } from "../intelligence-tab";

const mockGetAccount = getCompanyAccountIntelligence as jest.MockedFunction<
  typeof getCompanyAccountIntelligence
>;
const mockRecordEvidence = recordCompanyAccountEvidence as jest.MockedFunction<
  typeof recordCompanyAccountEvidence
>;

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <ToastProvider>
      <QueryClientProvider client={queryClient}>
        <IntelligenceTab companyId="co-1" />
      </QueryClientProvider>
    </ToastProvider>
  );
}

describe("company account intelligence tab", () => {
  beforeEach(() => jest.clearAllMocks());

  it("renders persisted CRM counts and explains missing data without inventing a score", async () => {
    mockGetAccount.mockResolvedValue({
      company_id: "co-1",
      company_name: "Test Co",
      industry: "Technology",
      city: "Riyadh",
      company_status: "active",
      total_opportunities: 2,
      active_opportunities: 1,
      won_deals: 1,
      lost_deals: 0,
      activity_count: 3,
      last_activity_at: "2026-09-20T10:00:00+00:00",
      days_since_activity: 1,
      missing_data: [],
      account_signals: {
        status: "engaged",
        signals: [
          {
            code: "RECENT_ACTIVITY",
            polarity: "positive",
            title: "Recent account engagement",
            detail: "A company activity was recorded 1 day ago.",
            source: "activity_records",
          },
        ],
        recommendations: [],
      },
      engagement_trend: {
        trend: "improving",
        recent_90_days: 3,
        previous_90_days: 1,
        change_percent: 200,
        method: "activity_count_90d_comparison_v1",
        interpretation: "Activity volume only; it does not measure customer sentiment or deal quality.",
      },
      generated_at: "2026-09-21T10:00:00+00:00",
      method: "persisted_crm_records_with_explainable_rules",
      mutated_crm: false,
    });

    renderTab();

    expect(await screen.findByRole("heading", { name: "CRM account facts" })).toBeInTheDocument();
    expect(screen.getByText("Test Co · Technology · Riyadh")).toBeInTheDocument();
    expect(screen.getByText("Open opportunities")).toBeInTheDocument();
    expect(
      screen.getByText(/Signals are deterministic rules over persisted CRM records/)
    ).toHaveTextContent(/No predictive score is calculated/);
    expect(screen.getByTestId("account-signals")).toHaveTextContent("Recent account engagement");
    expect(screen.getByTestId("engagement-trend")).toHaveTextContent("+200%");
    expect(screen.queryByText(/health score|expected revenue/i)).not.toBeInTheDocument();
  });

  it("shows each missing history section as a data gap", async () => {
    mockGetAccount.mockResolvedValue({
      company_id: "co-1",
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
        status: "insufficient_data",
        signals: [
          {
            code: "NO_OPPORTUNITY_HISTORY",
            polarity: "neutral",
            title: "No opportunity history",
            detail: "No opportunities are linked to this account in the tenant CRM.",
            source: "commercial_opportunities",
          },
          {
            code: "NO_ACTIVITY_HISTORY",
            polarity: "neutral",
            title: "No activity recorded",
            detail: "No company activity is recorded in the tenant CRM.",
            source: "activity_records",
          },
        ],
        recommendations: [],
      },
      engagement_trend: {
        trend: "insufficient_data",
        recent_90_days: 0,
        previous_90_days: 0,
        change_percent: null,
        method: "activity_count_90d_comparison_v1",
        interpretation: "Activity volume only; it does not measure customer sentiment or deal quality.",
      },
      generated_at: "2026-09-21T10:00:00+00:00",
      method: "persisted_crm_records_with_explainable_rules",
      mutated_crm: false,
    });

    renderTab();

    expect(await screen.findByText("No opportunities are linked to this company yet.")).toBeInTheDocument();
    expect(screen.getByText("No company activity is recorded yet.")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("engagement-trend")).getByText("insufficient data")
    ).toBeInTheDocument();
  });

  it("records the displayed account signals into the evidence chain on request", async () => {
    mockGetAccount.mockResolvedValue({
      company_id: "co-1",
      company_name: "Test Co",
      industry: null,
      city: null,
      company_status: "active",
      total_opportunities: 1,
      active_opportunities: 1,
      won_deals: 0,
      lost_deals: 0,
      activity_count: 0,
      last_activity_at: null,
      days_since_activity: null,
      missing_data: ["activity_history"],
      account_signals: {
        status: "needs_attention",
        signals: [
          {
            code: "OPEN_DEALS_WITHOUT_RECENT_ACTIVITY",
            polarity: "attention",
            title: "Open opportunities need follow-up",
            detail: "1 open opportunity has no activity recorded within the last 90 days.",
            source: "commercial_opportunities+activity_records",
          },
          {
            code: "NO_ACTIVITY_HISTORY",
            polarity: "neutral",
            title: "No activity recorded",
            detail: "No company activity is recorded in the tenant CRM.",
            source: "activity_records",
          },
        ],
        recommendations: ["Review the open opportunities and record the next customer action."],
      },
      engagement_trend: {
        trend: "insufficient_data",
        recent_90_days: 0,
        previous_90_days: 0,
        change_percent: null,
        method: "activity_count_90d_comparison_v1",
        interpretation: "Activity volume only; it does not measure customer sentiment or deal quality.",
      },
      generated_at: "2026-09-21T10:00:00+00:00",
      method: "persisted_crm_records_with_explainable_rules",
      mutated_crm: false,
    });
    mockRecordEvidence.mockResolvedValue({
      insight_id: "insight-1",
      created: true,
      evidence_count: 2,
      overall_confidence: 0.55,
      confidence_level: "medium",
      idempotency_key: "account-signals-v1:key",
    });

    renderTab();
    fireEvent.click(await screen.findByTestId("record-account-evidence"));

    await waitFor(() => expect(mockRecordEvidence).toHaveBeenCalledWith("co-1", "tenant-1"));
    expect(await screen.findByText(/Evidence snapshot recorded/)).toBeInTheDocument();
  });
});
