import { render, screen } from "@testing-library/react";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "c-1" }),
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock("next/link", () => {
  function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  }
  MockLink.displayName = "MockLink";
  return MockLink;
});

jest.mock("@/lib/hooks/companyQueries", () => ({
  useCompany: () => ({
    data: {
      id: "c-1",
      name_ar: "شركة الاختبار",
      name_en: "Test Co",
      confidence_score: 0.8,
    },
    isLoading: false,
    isError: false,
  }),
}));

const mockUseCompany360 = jest.fn();
jest.mock("@/lib/hooks/company360Queries", () => ({
  useCompany360: (...args: unknown[]) => mockUseCompany360(...args),
}));

jest.mock("@/features/company-intelligence/widgets/company-360/KnowledgeGraphPanel", () => ({
  KnowledgeGraphPanel: () => <div data-testid="kg-panel" />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/ActivityTimeline", () => ({
  ActivityTimeline: () => <div data-testid="activity-timeline" />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/DecisionPlatformPanel", () => ({
  DecisionPlatformPanel: () => <div data-testid="decision-panel" />,
}));
jest.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@salesos/ui", () => {
  const actual = jest.requireActual("@salesos/ui") as Record<string, unknown>;
  return {
    ...actual,
    Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Tab: ({ children }: { children: React.ReactNode }) => <button type="button">{children}</button>,
    TabsPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

import Company360Page from "../page";

const base360 = {
  overview: {
    total_contacts: 1,
    total_opportunities: 0,
    total_revenue: 0,
    active_contracts: 0,
    pending_tasks: 0,
    upcoming_meetings: 0,
    last_activity: null,
    signal_count: 0,
    contacts_page: 1,
    contacts_total: 0,
    opportunities_page: 1,
    opportunities_total: 0,
    timeline_page: 1,
    timeline_total: 0,
  },
  organization: {
    branches: [],
    departments: [],
    employees_count: 0,
    legal_form: null,
    incorporation_date: null,
  },
  contacts: [],
  opportunities: [],
  contracts: [],
  invoices: [],
};

describe("Company 360 signals badge", () => {
  beforeEach(() => {
    mockUseCompany360.mockReset();
  });

  it("shows the count badge when signals.total is positive", () => {
    mockUseCompany360.mockReturnValue({
      data: { ...base360, signals: { items: [{ title: "hit" }], total: 7 } },
      isLoading: false,
      isError: false,
    });
    render(<Company360Page />);
    expect(screen.getByText("الإشارات")).toBeInTheDocument();
    expect(screen.getByTestId("company360-signals-badge")).toHaveTextContent("7");
  });

  it("hides the badge when signals is omitted (Vercel optional total)", () => {
    mockUseCompany360.mockReturnValue({
      data: { ...base360 },
      isLoading: false,
      isError: false,
    });
    render(<Company360Page />);
    expect(screen.getByText("الإشارات")).toBeInTheDocument();
    expect(screen.queryByTestId("company360-signals-badge")).not.toBeInTheDocument();
  });

  it("renders settings info from company fields instead of EmptyState", () => {
    mockUseCompany360.mockReturnValue({
      data: {
        ...base360,
        assigned_employees: [{ full_name: "أحمد" }],
        company: { tags: ["vip"] },
      },
      isLoading: false,
      isError: false,
    });
    render(<Company360Page />);
    const panel = screen.getByTestId("company360-settings-panel");
    expect(panel).toHaveTextContent("الاسم");
    expect(panel).toHaveTextContent("شركة الاختبار");
    expect(panel).toHaveTextContent("المالك");
    expect(panel).toHaveTextContent("أحمد");
    expect(panel).toHaveTextContent("الوسوم");
    expect(panel).toHaveTextContent("vip");
    expect(screen.queryByText("إعدادات الشركة")).not.toBeInTheDocument();
  });
});
