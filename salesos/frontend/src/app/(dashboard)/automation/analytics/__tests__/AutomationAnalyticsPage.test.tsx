import { render, screen, waitFor } from "@testing-library/react";
import AutomationAnalyticsPage from "../page";

const mockGet = jest.fn();

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: { get: (...args: any[]) => mockGet(...args) },
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "test-tenant",
}));

jest.mock("@/lib/workflowQueries", () => ({
  useWorkflows: () => ({
    data: [
      {
        id: "wf-1",
        name: "متابعة العميل",
        status: "active",
        steps: [],
        trigger_type: "event",
        trigger_config: {},
        created_at: "",
        updated_at: "",
      },
      {
        id: "wf-2",
        name: "مراجعة الصفقة",
        status: "draft",
        steps: [],
        trigger_type: "manual",
        trigger_config: {},
        created_at: "",
        updated_at: "",
      },
    ],
    isLoading: false,
  }),
  useWorkflowExecutions: () => ({
    data: [],
    isLoading: false,
  }),
}));

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}));

jest.mock("@salesos/ui", () => ({
  cn: (...args: (string | undefined | false)[]) =>
    args.filter(Boolean).join(" "),
  Badge: ({ children, variant }: any) => (
    <span data-variant={variant}>{children}</span>
  ),
  Button: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
}));

jest.mock("@salesos/charts", () => ({
  BarChart: ({ title }: any) => <div data-testid="bar-chart">{title}</div>,
  LineChart: ({ title }: any) => <div data-testid="line-chart">{title}</div>,
  PieChart: ({ title }: any) => <div data-testid="pie-chart">{title}</div>,
  MetricCard: ({ label, value }: any) => (
    <div data-testid="metric-card">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  ),
}));

jest.mock("lucide-react", () => ({
  ArrowLeft: () => <svg data-testid="icon-arrow-left" />,
  Workflow: () => <svg data-testid="icon-workflow" />,
  CheckCircle: () => <svg data-testid="icon-check" />,
  Clock: () => <svg data-testid="icon-clock" />,
  Play: () => <svg data-testid="icon-play" />,
}));

jest.mock("next/link", () => {
  function MockLink({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  }
  MockLink.displayName = "MockLink";
  return MockLink;
});

const sampleAnalytics = {
  total_workflows: 2,
  active_workflows: 1,
  draft_workflows: 1,
  total_executions: 10,
  successful_executions: 8,
  failed_executions: 2,
  completion_rate: 80,
  avg_duration_seconds: 45,
  failure_rate: 20,
  executions_over_time: [],
  top_workflows: [] as {
    id: string;
    name: string;
    runs: number;
    success_rate: number;
  }[],
  recent_executions: [],
};

describe("AutomationAnalyticsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("1. Loading state", () => {
    it("shows loading skeletons", () => {
      mockGet.mockReturnValue(new Promise(() => {}));
      render(<AutomationAnalyticsPage />);
      expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
    });
  });

  describe("2. Loaded state", () => {
    it("renders the page title", async () => {
      mockGet.mockResolvedValue({ data: sampleAnalytics });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(screen.getByText("تحليلات الأتمتة")).toBeInTheDocument();
      });
    });

    it("renders back link", async () => {
      mockGet.mockResolvedValue({ data: sampleAnalytics });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        const links = screen.getAllByRole("link");
        const backLink = links.find(
          (l) => l.getAttribute("href") === "/automation",
        );
        expect(backLink).toBeTruthy();
      });
    });

    it("renders metric cards", async () => {
      mockGet.mockResolvedValue({
        data: {
          ...sampleAnalytics,
          total_workflows: 5,
          active_workflows: 3,
          draft_workflows: 2,
          total_executions: 50,
          successful_executions: 45,
          failed_executions: 5,
          completion_rate: 90,
          avg_duration_seconds: 120,
          failure_rate: 10,
        },
      });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        const metricCards = screen.getAllByTestId("metric-card");
        expect(metricCards.length).toBe(4);
      });
    });

    it("renders the completion gauge", async () => {
      mockGet.mockResolvedValue({
        data: {
          ...sampleAnalytics,
          total_workflows: 1,
          active_workflows: 1,
          draft_workflows: 0,
          total_executions: 20,
          successful_executions: 18,
          completion_rate: 90,
          avg_duration_seconds: 30,
          failure_rate: 10,
        },
      });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(screen.getByText("نسبة الإتمام")).toBeInTheDocument();
      });
    });

    it("renders the failure rate trend chart", async () => {
      mockGet.mockResolvedValue({ data: sampleAnalytics });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(screen.getByTestId("line-chart")).toHaveTextContent(
          "معدل الفشل على مدار الوقت",
        );
      });
    });

    it("renders the execution history table", async () => {
      mockGet.mockResolvedValue({
        data: {
          ...sampleAnalytics,
          total_workflows: 1,
          active_workflows: 1,
          draft_workflows: 0,
          total_executions: 5,
          successful_executions: 4,
          failed_executions: 1,
        },
      });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(screen.getByText("سجل التنفيذ الأخير")).toBeInTheDocument();
      });
    });

    it("renders top workflows table", async () => {
      mockGet.mockResolvedValue({
        data: {
          ...sampleAnalytics,
          active_workflows: 2,
          draft_workflows: 0,
          total_executions: 20,
          successful_executions: 18,
          completion_rate: 90,
          failure_rate: 10,
          top_workflows: [
            { id: "wf-1", name: "متابعة العميل", runs: 15, success_rate: 93 },
            { id: "wf-2", name: "مراجعة الصفقة", runs: 5, success_rate: 80 },
          ],
        },
      });
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(
          screen.getByText("أكثر سير العمل استخداماً"),
        ).toBeInTheDocument();
        expect(screen.getByText("متابعة العميل")).toBeInTheDocument();
      });
    });
  });

  describe("3. API error handling", () => {
    it("falls back gracefully when analytics API fails", async () => {
      mockGet.mockRejectedValue(new Error("API error"));
      render(<AutomationAnalyticsPage />);
      await waitFor(() => {
        expect(screen.getByText("تحليلات الأتمتة")).toBeInTheDocument();
      });
    });
  });
});
