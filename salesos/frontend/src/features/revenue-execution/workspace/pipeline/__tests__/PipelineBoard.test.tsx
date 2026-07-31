import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PipelineWorkspace } from "../PipelineWorkspace";

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn(),
    replace: jest.fn(),
  }),
}));

jest.mock("next/link", () => {
  const MockLink = ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>;
  MockLink.displayName = "MockLink";
  return MockLink;
});

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

jest.mock("@salesos/charts", () => ({
  MetricCard: ({ label, value }: any) => (
    <div data-testid="metric-card">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  ),
  BarChart: () => <div data-testid="bar-chart" />,
  LineChart: () => <div data-testid="line-chart" />,
  PieChart: () => <div data-testid="pie-chart" />,
}));

jest.mock("@/lib/hooks/opportunityQueries", () => ({
  useAdvanceOpportunity: jest.fn(),
  useCloseWon: jest.fn(),
  useCloseLost: jest.fn(),
}));

import api from "@/lib/api";
import {
  useAdvanceOpportunity,
  useCloseWon,
  useCloseLost,
} from "@/lib/hooks/opportunityQueries";

const mockApiGet = api.get as jest.Mock;
const mockUseAdvanceOpp = useAdvanceOpportunity as jest.Mock;
const mockUseCloseWon = useCloseWon as jest.Mock;
const mockUseCloseLost = useCloseLost as jest.Mock;

function makeOpp(overrides: Record<string, unknown> = {}) {
  return {
    id: "opp-1",
    name: "Test Deal",
    value: 500000,
    stage: "lead",
    status: "open",
    company_name: "Acme Corp",
    company_id: "comp-1",
    expected_close_date: "2026-08-01",
    ...overrides,
  };
}

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

function setupApiMocks(
  overrides: {
    opportunities?: any[];
    health?: any[];
    forecast?: any;
    analytics?: any;
  } = {},
) {
  const {
    opportunities = [],
    health = [],
    forecast = null,
    analytics = null,
  } = overrides;

  mockApiGet.mockImplementation((url: string) => {
    if (url === "/api/v1/opportunities")
      return Promise.resolve({ data: opportunities });
    if (url === "/api/v1/pipeline/health")
      return Promise.resolve({ data: health });
    if (url === "/api/v1/pipeline/forecast")
      return Promise.resolve({ data: forecast });
    if (url === "/api/v1/pipeline/analytics")
      return Promise.resolve({ data: analytics });
    return Promise.resolve({ data: null });
  });
}

describe("PipelineWorkspace", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupApiMocks();
    mockUseAdvanceOpp.mockReturnValue({ mutate: jest.fn() });
    mockUseCloseWon.mockReturnValue({ mutate: jest.fn() });
    mockUseCloseLost.mockReturnValue({ mutate: jest.fn() });
  });

  it("shows loading skeleton", () => {
    mockApiGet.mockImplementation(() => new Promise(() => {}));
    renderWithQuery(<PipelineWorkspace />);
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders 6 kanban columns after loading", async () => {
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("Opportunity")).toBeInTheDocument();
    });
    expect(screen.getByText("Lead")).toBeInTheDocument();
    expect(screen.getByText("Proposal")).toBeInTheDocument();
    expect(screen.getByText("Negotiation")).toBeInTheDocument();
    expect(screen.getByText("Closed Won")).toBeInTheDocument();
    expect(screen.getByText("Closed Lost")).toBeInTheDocument();
  });

  it("renders deal cards in correct columns", async () => {
    setupApiMocks({
      opportunities: [
        makeOpp({ id: "o1", name: "Deal Alpha", stage: "lead" }),
        makeOpp({ id: "o2", name: "Deal Beta", stage: "proposal" }),
      ],
    });
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("Deal Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("Deal Beta")).toBeInTheDocument();
  });

  it("calculates pipeline value correctly", async () => {
    setupApiMocks({
      opportunities: [
        makeOpp({ id: "o1", value: 100000, stage: "lead" }),
        makeOpp({ id: "o2", value: 200000, stage: "opportunity" }),
      ],
    });
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getAllByText(/300K SAR/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows empty drop zones when no opportunities", async () => {
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("Lead")).toBeInTheDocument();
    });
    expect(
      screen.getAllByText("Drop deals here").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("toggles between Kanban and Table view", async () => {
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("Lead")).toBeInTheDocument();
    });
    const toggleBtn = screen.getByRole("button", { name: /table/i });
    fireEvent.click(toggleBtn);
    expect(screen.getByRole("button", { name: /board/i })).toBeInTheDocument();
  });

  it("shows header with open deals count", async () => {
    setupApiMocks({
      opportunities: [
        makeOpp({ id: "o1", stage: "lead" }),
        makeOpp({ id: "o2", stage: "opportunity" }),
      ],
    });
    renderWithQuery(<PipelineWorkspace />);
    await waitFor(() => {
      expect(screen.getByText(/open deals/)).toBeInTheDocument();
    });
  });
});
