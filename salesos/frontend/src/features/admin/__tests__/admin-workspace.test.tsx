import { render, screen } from "@testing-library/react";

// Pin Arabic admin.tab.* copy so this suite does not depend on jest.setup
// mock ordering under full-suite --coverage runs.
jest.mock("@/lib/i18n", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const ar = require("@/lib/i18n/ar.json") as Record<string, string>;
  return {
    useTranslation: () => ({
      t: (key: string) => ar[key] ?? key,
      locale: "ar" as const,
      setLocale: () => {},
      dir: "rtl" as const,
    }),
  };
});

jest.mock("@/lib/hooks/adminQueries", () => ({
  useAdminTenants: () => ({ data: [], isLoading: false }),
  useAdminPlans: () => ({ data: [], isLoading: false }),
  useAdminUsers: () => ({ data: [], isLoading: false }),
  useAdminDetailedHealth: () => ({ data: null, isLoading: false }),
  useAdminLicenses: () => ({ data: [], isLoading: false }),
  useAdminFeatureFlags: () => ({ data: [], isLoading: false }),
  useAdminFlagTenants: () => ({ data: [], isLoading: false }),
  useAdminJobs: () => ({ data: [], isLoading: false }),
  useAdminJobDetail: () => ({ data: null, isLoading: false }),
  useAdminAICosts: () => ({ data: [], isLoading: false }),
  useAdminAICostSummary: () => ({ data: null, isLoading: false }),
  useAdminAIUsage: () => ({ data: null, isLoading: false }),
  useAdminHealthHistory: () => ({ data: [], isLoading: false }),
  useCreateAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDeleteAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminPlan: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateAdminPlan: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminLicense: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDeactivateAdminUser: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminFeatureFlag: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useToggleAdminFlagForTenant: () => ({ mutate: jest.fn(), isPending: false }),
  useRetryAdminJob: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

import { AdminWorkspace } from "../AdminWorkspace";

describe("AdminWorkspace", () => {
  it("renders overview with quick actions", () => {
    render(<AdminWorkspace />);
    expect(screen.getByText("لوحة الإدارة")).toBeInTheDocument();
    expect(screen.getByText("إجراءات سريعة")).toBeInTheDocument();
  });

  it("exposes EPIC-07 MVP deep-links on overview", () => {
    render(<AdminWorkspace />);
    expect(screen.getByTestId("owner-console-mvp-links")).toBeInTheDocument();
    expect(
      screen.getByTestId("owner-console-overview-tenants"),
    ).toHaveAttribute("href", "/admin/tenants");
    expect(
      screen.getByTestId("owner-console-overview-billing"),
    ).toHaveAttribute("href", "/admin/billing");
    expect(screen.getByTestId("owner-console-overview-flags")).toHaveAttribute(
      "href",
      "/admin/flags",
    );
    expect(screen.getByTestId("owner-console-overview-config")).toHaveAttribute(
      "href",
      "/admin/config",
    );
    expect(screen.getByTestId("owner-console-overview-audit")).toHaveAttribute(
      "href",
      "/admin/audit",
    );
  });

  it("renders sidebar navigation tabs", () => {
    render(<AdminWorkspace />);
    // Labels come from ar.json via useTranslation (admin.tab.*)
    // Sidebar + overview quick-actions can render the same labels twice
    expect(screen.getAllByText("نظرة عامة").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("العملاء").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("الباقات").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("المستخدمين").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("الميزات التجريبية").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("الوظائف الخلفية").length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("تكاليف AI").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("صحة النظام").length).toBeGreaterThanOrEqual(1);
  });
});
