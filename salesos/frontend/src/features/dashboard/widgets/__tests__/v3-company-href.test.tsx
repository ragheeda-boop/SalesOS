import { fireEvent, render, screen } from "@testing-library/react";

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock("../widget-card", () => ({
  WidgetCard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock("../../_providers/dashboard-provider", () => ({
  useDashboardContext: () => ({
    widgets: {
      recentActivity: {
        status: "ready",
        data: {
          items: [
            {
              id: "a1",
              type: "signal",
              title: "إشارة مناقصة جديدة من أرامكو",
              companyId: "c-ra",
              companyName: "أرامكو السعودية",
              timestamp: "2026-07-10T08:30:00.000Z",
            },
          ],
          total: 1,
        },
      },
      decisionQueue: {
        status: "ready",
        data: {
          items: [
            {
              id: "d1",
              companyId: "c-dq",
              companyName: "ACME Corp",
              type: "opportunity",
              title: "صفقة استراتيجية كبرى",
              priority: "high",
              score: 92,
            },
          ],
          total: 1,
        },
      },
      pipeline: {
        status: "ready",
        data: {
          stages: [],
          deals: [
            {
              id: "deal1",
              companyId: "c-pl",
              companyName: "ACME Corp",
              title: "صفقة الاستحواذ",
              stage: "تقديم عرض",
              value: 1000,
              probability: 75,
              daysInStage: 1,
            },
          ],
          totalValue: 1000,
          dealCount: 1,
        },
      },
      marketPulse: {
        status: "ready",
        data: {
          trends: [],
          topMovers: [
            {
              companyId: "c-mp",
              companyName: "أرامكو",
              scoreChange: 15,
              reason: "نتائج قوية",
            },
          ],
        },
      },
      companyHealth: {
        status: "ready",
        data: {
          overallScore: 76,
          metrics: [],
          alerts: [
            {
              id: "al1",
              type: "critical",
              message: "صفقة بقيمة 2M معرضة للخسارة",
              companyId: "c-ch",
              companyName: "ACME Corp",
              timestamp: "2026-07-13T00:00:00Z",
            },
          ],
          companyName: "ACME Corp",
        },
      },
    },
  }),
}));

jest.mock("../../../revenue-execution/_providers/DecisionProvider", () => ({
  useCompanyDecision: () => null,
}));

jest.mock("../../_hooks/useNBAFeed", () => ({
  useNBAFeed: () => [],
}));

import { v3CompanyHref } from "../v3-company-href";
import { RecentActivityWidget } from "../recent-activity/RecentActivityContainer";
import { DecisionQueueWidget } from "../decision-queue/DecisionQueueContainer";
import { PipelineWidget } from "../pipeline/PipelineContainer";
import { MarketPulseWidget } from "../market-pulse/MarketPulseContainer";
import { CompanyHealthWidget } from "../company-health/CompanyHealthContainer";

function stubLocation() {
  const hrefs: string[] = [];
  Object.defineProperty(window, "location", {
    configurable: true,
    value: {
      get href() {
        return hrefs.at(-1) ?? "";
      },
      set href(value: string) {
        hrefs.push(value);
      },
    },
  });
  return hrefs;
}

describe("leftover dashboard widget company 360 href", () => {
  it("retargets leftover /companies/{id} to /v3/companies/{id}", () => {
    expect(v3CompanyHref("c1")).toBe("/v3/companies/c1");
    expect(v3CompanyHref("c1").startsWith("/companies/")).toBe(false);
  });

  it("dumps leftover widget clicks to /v3/companies/{id} only", () => {
    const hrefs = stubLocation();

    render(<RecentActivityWidget />);
    fireEvent.click(screen.getByLabelText(/إشارة مناقصة جديدة من أرامكو/));
    expect(hrefs.at(-1)).toBe("/v3/companies/c-ra");

    render(<DecisionQueueWidget />);
    fireEvent.click(screen.getByLabelText(/صفقة استراتيجية كبرى/));
    expect(hrefs.at(-1)).toBe("/v3/companies/c-dq");

    render(<PipelineWidget />);
    fireEvent.click(screen.getByLabelText(/صفقة الاستحواذ/));
    expect(hrefs.at(-1)).toBe("/v3/companies/c-pl");

    render(<MarketPulseWidget />);
    fireEvent.click(screen.getByLabelText(/أرامكو - تحسن 15 نقطة/));
    expect(hrefs.at(-1)).toBe("/v3/companies/c-mp");

    render(<CompanyHealthWidget />);
    fireEvent.click(screen.getByLabelText(/حرج/));
    expect(hrefs.at(-1)).toBe("/v3/companies/c-ch");

    expect(hrefs.some((href) => /^\/companies\//.test(href))).toBe(false);
  });
});
