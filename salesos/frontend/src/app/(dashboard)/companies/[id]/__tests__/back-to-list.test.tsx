import { render, screen } from "@testing-library/react";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "c-1" }),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock("@/lib/hooks/companyQueries", () => ({
  useCompany: () => ({ data: { id: "c-1", name_ar: "شركة الاختبار", name_en: "Test Co" } }),
}));

jest.mock("@/lib/hooks/mutationHooks", () => ({
  useUpdateCompany: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDeleteCompany: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useAddContact: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

jest.mock("@/lib/hooks/opportunityQueries", () => ({
  useCreateOpportunity: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

jest.mock("@/components/company-workspace", () => ({
  CompanyWorkspace: () => <div data-testid="workspace" />,
}));

jest.mock("@/features/revenue-execution/_providers/DecisionProvider", () => ({
  DecisionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@/components/foundation/error-boundary", () => ({
  ErrorFallback: () => <div />,
}));

jest.mock("@/features/tenant-studio/CustomFieldsAutoRender", () => ({
  CustomFieldsAutoRender: () => null,
}));

import LeftoverCompanyPage from "../page";

describe("leftover company workspace back-to-list", () => {
  it("sends leftover 360 users to /v3/companies instead of leftover /companies", () => {
    render(<LeftoverCompanyPage />);

    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(screen.getByRole("link", { name: /companies\.back_to_list/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
  });
});
