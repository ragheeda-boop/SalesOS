import { fireEvent, render, screen } from "@testing-library/react";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "c-1" }),
  useRouter: () => ({ push }),
}));

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock("@/lib/hooks/companyQueries", () => ({
  useCompany: () => ({ data: null, isLoading: false, isError: true }),
}));

jest.mock("@/lib/hooks/company360Queries", () => ({
  useCompany360: () => ({ data: null, isLoading: false, isError: true }),
}));

jest.mock("@/features/company-intelligence/widgets/company-360/KnowledgeGraphPanel", () => ({
  KnowledgeGraphPanel: () => <div />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/ActivityTimeline", () => ({
  ActivityTimeline: () => <div />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/DecisionPlatformPanel", () => ({
  DecisionPlatformPanel: () => <div />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/Company360DocumentList", () => ({
  Company360DocumentList: () => <div />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/Company360NextStepsList", () => ({
  Company360NextStepsList: () => <div />,
}));
jest.mock("@/features/company-intelligence/widgets/company-360/Company360SettingsPanel", () => ({
  Company360SettingsPanel: () => <div />,
}));
jest.mock("@/components/error-boundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import Company360Page from "../page";

describe("leftover company 360 back-to-list", () => {
  beforeEach(() => {
    push.mockReset();
  });

  it("sends leftover 360 list CTAs to /v3/companies", () => {
    render(<Company360Page />);

    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(screen.getByRole("link", { name: "nav.companies" })).toHaveAttribute("href", "/v3/companies");

    fireEvent.click(screen.getByRole("button", { name: "companies.back_to_list" }));
    expect(push).toHaveBeenCalledWith("/v3/companies");
    expect(push).not.toHaveBeenCalledWith("/companies");
  });
});
