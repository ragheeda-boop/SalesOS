import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));
jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "tenant" }),
}));
jest.mock("@/lib/api", () => ({ listCommercialEvidence: jest.fn() }));

import { listCommercialEvidence } from "@/lib/api";
import EvidencePage from "../page";

const mockList = listCommercialEvidence as jest.MockedFunction<typeof listCommercialEvidence>;

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <EvidencePage />
    </QueryClientProvider>
  );
}

describe("Evidence page", () => {
  beforeEach(() => jest.clearAllMocks());

  it("shows persisted insight, classified source evidence, and target link", async () => {
    mockList.mockResolvedValue({
      items: [{
        id: "insight-1",
        category: "deal_risk",
        title: "Stalled deal",
        description: "No activity recorded in the current stage.",
        target_id: "deal-1",
        target_type: "opportunity",
        overall_confidence: 0.7,
        confidence_level: "medium",
        created_at: "2026-09-21T10:00:00+00:00",
        updated_at: "2026-09-21T10:00:00+00:00",
        evidence_items: [{
          id: "evidence-1",
          evidence_type: "activity_signal",
          source_domain: "activity",
          source_type: "table_aggregate",
          source_id: "activity-1",
          source_name: "CRM activity",
          description: "No activity recorded in the current stage.",
          confidence: 0.6,
          confidence_level: "medium",
          evidence_kind: "crm.system_of_record",
          recorded_at: "2026-09-21T10:00:00+00:00",
        }],
      }],
      total: 1,
      page: 1,
      page_size: 20,
      read_only: true,
    });

    renderPage();

    expect(await screen.findByRole("heading", { name: "Evidence chain" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Stalled deal" })).toBeInTheDocument();
    expect(screen.getByText(/crm\.system_of_record/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open deal" })).toHaveAttribute(
      "href",
      "/v3/crm/deal-1"
    );
  });

  it("applies tenant-scoped filters and reports an empty result honestly", async () => {
    mockList.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      read_only: true,
    });

    renderPage();

    expect(await screen.findByText("No persisted insights")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Target type"), { target: { value: "company" } });
    fireEvent.change(screen.getByLabelText("Target ID"), { target: { value: "co-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));

    await screen.findByText("No persisted insights");
    expect(mockList).toHaveBeenLastCalledWith("tenant-1", expect.objectContaining({
      target_type: "company",
      target_id: "co-1",
    }));
  });
});
