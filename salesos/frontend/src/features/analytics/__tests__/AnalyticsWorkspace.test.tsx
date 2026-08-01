import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AnalyticsWorkspace } from "../AnalyticsWorkspace";

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "analytics.title": "Analytics",
        "analytics.subtitle":
          "Key performance indicators and advanced analytics dashboards",
        "analytics.revenue": "Revenue",
        "analytics.pipeline": "Pipeline",
        "analytics.conversion": "Conversion Rate",
        "analytics.avg_deal_size": "Avg Deal Size",
        "analytics.pipeline_stages": "Pipeline Stages",
        "analytics.total_deals": "Total Deals",
        "analytics.won_deals": "Won",
        "analytics.lost_deals": "Lost",
        "analytics.growth": "Growth",
        "analytics.risk_overview": "Risk Overview",
        "analytics.team_overview": "Team Overview",
        "analytics.renewals": "Renewals",
        "analytics.forecast": "Forecast",
        "analytics.no_data": "No data",
        "common.export": "Export",
      };
      return map[key] || key;
    },
    dir: "ltr",
  }),
}));

jest.mock("@salesos/charts", () => ({
  BarChart: () => <div data-testid="bar-chart" />,
  PieChart: () => <div data-testid="pie-chart" />,
  MetricCard: ({ label, value }: { label: string; value: string | number }) => (
    <div data-testid="metric-card">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  ),
}));

jest.mock("@/lib/hooks/executiveQueries", () => ({
  useExecutiveDashboard: jest.fn(),
}));

import { useExecutiveDashboard } from "@/lib/hooks/executiveQueries";

const mockUseExecutiveDashboard = useExecutiveDashboard as jest.MockedFunction<
  typeof useExecutiveDashboard
>;

const dashboardFixture = {
  revenue: {
    total_booked: 12_500_000,
    total_pipeline: 42_000_000,
    weighted_pipeline: 30_000_000,
    forecast: 15_000_000,
    growth_percent: 12,
  },
  pipeline: {
    total_deals: 100,
    total_value: 42_000_000,
    won_deals: 33,
    lost_deals: 17,
    win_rate: 33,
    avg_deal_size: 420_000,
    by_stage: [
      { stage: "Qualify", val: 10 },
      { stage: "Propose", val: 20 },
    ],
  },
  growth: {
    new_companies_30d: 10,
    new_contacts_30d: 25,
    new_opportunities_30d: 5,
    new_contracts_30d: 3,
  },
  risk: {
    stalled_deals: 5,
    expiring_contracts: 3,
    inactive_companies: 2,
    low_pipeline_employees: 1,
  },
  team: {
    total_employees: 50,
    active_employees: 45,
    top_performers: [],
    avg_win_rate: 40,
  },
  renewals: {
    due_next_30_days: 2,
    due_next_90_days: 5,
    total_renewal_value: 500_000,
    at_risk: [],
  },
  health: {
    overall_health: "good",
    data_completeness: 85,
    sync_status: "synced",
    last_activity: "2026-07-10",
  },
};

function renderWorkspace() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AnalyticsWorkspace />
    </QueryClientProvider>,
  );
}

describe("AnalyticsWorkspace", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // mockImplementation holds under --coverage better than one-shot return
    mockUseExecutiveDashboard.mockImplementation(
      () =>
        ({
          data: dashboardFixture,
          isLoading: false,
          error: null,
        }) as ReturnType<typeof useExecutiveDashboard>,
    );
  });

  it("renders title", () => {
    renderWorkspace();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
  });

  it("renders KPI cards from executive dashboard data", () => {
    renderWorkspace();
    expect(screen.getAllByText("$12.5M").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("$42.0M")).toBeInTheDocument();
    expect(screen.getByText("33%")).toBeInTheDocument();
    expect(screen.getByText("$420K")).toBeInTheDocument();
  });

  it("renders export control", () => {
    renderWorkspace();
    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("renders chart sections", () => {
    renderWorkspace();
    expect(screen.getByText("Pipeline Stages")).toBeInTheDocument();
    expect(screen.getByText("Growth")).toBeInTheDocument();
    expect(screen.getByText("Risk Overview")).toBeInTheDocument();
  });

  it("has accessible region", () => {
    renderWorkspace();
    expect(
      screen.getByRole("region", { name: "Analytics" }),
    ).toBeInTheDocument();
  });
});
