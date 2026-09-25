import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getOpportunityNBA, refreshOpportunityNBA } from "@/lib/api";
import { DealNbaTab } from "../nba-tab";

jest.mock("@/lib/api", () => ({
  getOpportunityNBA: jest.fn(),
  refreshOpportunityNBA: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({ getTenantId: () => "tenant-1" }));

const getNbaMock = getOpportunityNBA as jest.MockedFunction<typeof getOpportunityNBA>;
const refreshNbaMock = refreshOpportunityNBA as jest.MockedFunction<typeof refreshOpportunityNBA>;

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DealNbaTab opportunityId="opp-1" />
    </QueryClientProvider>
  );
}

describe("DealNbaTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getNbaMock.mockResolvedValue({
      id: "nba-1",
      opportunity_id: "opp-1",
      action: "schedule_follow_up",
      reason: "The opportunity has not had recent activity.",
      confidence: 0.72,
      confidence_label: "medium",
      source: "rule",
      alternatives: [],
      evidence: [{ type: "activity", description: "No activity in the last two weeks.", source: "activity_records", confidence: 0.8 }],
      potential_risks: [{ type: "stale", level: "medium", description: "The deal may be stalled." }],
      status: "pending",
      created_at: "2026-09-21T08:00:00Z",
      updated_at: "2026-09-21T08:00:00Z",
    });
  });

  it("shows the recommendation and the supporting evidence", async () => {
    renderTab();

    expect(await screen.findByText("Schedule Follow Up")).toBeInTheDocument();
    expect(screen.getByText("The opportunity has not had recent activity.")).toBeInTheDocument();
    expect(screen.getByText("No activity in the last two weeks.")).toBeInTheDocument();
    expect(screen.getByText(/does not send a message or change the opportunity/i)).toBeInTheDocument();
  });

  it("refreshes using the supported API and replaces the displayed recommendation", async () => {
    refreshNbaMock.mockResolvedValue({
      id: "nba-2",
      opportunity_id: "opp-1",
      action: "prepare_proposal",
      reason: "The buyer requested a proposal.",
      confidence: 0.8,
      confidence_label: "high",
      source: "rule",
      alternatives: [],
      evidence: [],
      potential_risks: [],
      status: "pending",
      created_at: "2026-09-21T08:00:00Z",
      updated_at: "2026-09-21T08:00:00Z",
    });
    renderTab();

    fireEvent.click(await screen.findByRole("button", { name: "Refresh recommendation" }));
    await waitFor(() => expect(refreshNbaMock).toHaveBeenCalledWith("opp-1", "tenant-1"));
    expect(await screen.findByText("Prepare Proposal")).toBeInTheDocument();
  });
});
