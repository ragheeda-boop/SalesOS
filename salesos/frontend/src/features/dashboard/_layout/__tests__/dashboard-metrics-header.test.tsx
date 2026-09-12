import { render, screen } from "@testing-library/react";

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock("../../_providers/dashboard-provider", () => ({
  useDashboardContext: () => ({
    widgets: {
      missionCenter: {
        data: {
          companiesTracked: 1,
          activeDeals: 0,
          pipelineValue: 0,
          signalsToday: 0,
          decisionsPending: 0,
        },
      },
    },
  }),
}));

import { DashboardMetricsHeader } from "../dashboard-metrics-header";

describe("leftover dashboard metrics header golden-path hubs", () => {
  it("retargets leftover new-company CTA to /v3/companies", () => {
    render(<DashboardMetricsHeader />);

    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(document.querySelector('a[href="/companies/new"]')).toBeNull();
    expect(document.querySelector('a[href="/dashboard"]')).toBeNull();
    expect(screen.getByRole("link", { name: /dashboard\.new_company/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
  });
});
