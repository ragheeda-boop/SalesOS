import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));
jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "tenant" }),
}));
jest.mock("@/lib/api", () => ({ listAIGovernanceAudit: jest.fn() }));

import { listAIGovernanceAudit } from "@/lib/api";
import AIGovernanceAuditPage from "../page";

const mockList = listAIGovernanceAudit as jest.MockedFunction<typeof listAIGovernanceAudit>;

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AIGovernanceAuditPage />
    </QueryClientProvider>
  );
}

describe("AI Governance Audit page", () => {
  beforeEach(() => jest.clearAllMocks());

  it("shows persisted policy metadata in a tenant-scoped read-only table", async () => {
    mockList.mockResolvedValue({
      items: [
        {
          id: 7,
          user_id: "user-1",
          action: "ai:policy:blocked",
          resource_type: "ai:governance/policy",
          resource_id: "policy-1",
          outcome: "success",
          request_id: "req-1",
          created_at: "2026-09-21T10:00:00+00:00",
          policy_name: "Outbound safety",
          decision: null,
          enforcement_action: "blocked",
        },
      ],
      total: 1,
      page: 1,
      page_size: 25,
      generated_at: "2026-09-21T10:00:00+00:00",
      read_only: true,
    });

    renderPage();

    expect(await screen.findByRole("heading", { name: "AI Governance Audit" })).toBeInTheDocument();
    expect(await screen.findByText("Outbound safety")).toBeInTheDocument();
    expect(screen.getByText("ai policy blocked")).toBeInTheDocument();
    expect(screen.getByText(/records are read-only/i)).toBeInTheDocument();
    expect(screen.queryByText("raw payload")).not.toBeInTheDocument();
  });

  it("renders an honest empty state", async () => {
    mockList.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 25,
      generated_at: "2026-09-21T10:00:00+00:00",
      read_only: true,
    });

    renderPage();

    expect(await screen.findByText("No AI governance events")).toBeInTheDocument();
  });
});
