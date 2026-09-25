import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { FactProposalPage } from "@/lib/factReviewQueries";
import FactReviewPage from "../page";
import { decideFactProposal, fetchFactProposals } from "@/lib/factReviewQueries";

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true }),
}));

jest.mock("@/lib/factReviewQueries", () => ({
  decideFactProposal: jest.fn(),
  fetchFactProposals: jest.fn(),
}));

const proposalPage: FactProposalPage = {
  items: [
    {
      id: "fact-1",
      subject_type: "company",
      subject_id: "company-7",
      field_name: "city",
      proposed_value: "الرياض",
      status: "PROPOSED",
      evidence_band: "STRONG",
      score: 0.92,
      decision_reason: "Two independent sources agree.",
      actor_type: "human",
      actor_id: "reviewer-2",
      evidence_snapshot: [
        {
          id: "evidence-1",
          evidence_kind: "first_party",
          description: "Company contact page",
          confidence: 0.9,
          source: { source_domain: "example.sa" },
        },
      ],
      created_at: "2026-09-21T12:00:00Z",
      reviewer_id: null,
      reviewed_at: null,
    },
  ],
  limit: 50,
  offset: 0,
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <FactReviewPage />
    </QueryClientProvider>,
  );
}

describe("Fact Review page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetchFactProposals as jest.Mock).mockResolvedValue(proposalPage);
    (decideFactProposal as jest.Mock).mockResolvedValue({
      id: "fact-1",
      status: "APPROVED",
      reviewed_at: "2026-09-21T12:01:00Z",
      changed: true,
      crm_applied: false,
    });
  });

  it("shows the proposed value, evidence, and no-CRM-apply boundary", async () => {
    renderPage();

    expect(await screen.findByText(/city: الرياض/)).toBeInTheDocument();
    expect(screen.getByText(/example\.sa/)).toBeInTheDocument();
    expect(screen.getByText(/لن تتغير بيانات Company أو Contact تلقائيًا/)).toBeInTheDocument();
  });

  it("requires a reason before posting a human decision", async () => {
    renderPage();
    const approve = await screen.findByRole("button", { name: "موافقة" });
    expect(approve).toBeDisabled();

    fireEvent.change(screen.getByLabelText("سبب القرار"), {
      target: { value: "Checked the official company page." },
    });
    expect(approve).toBeEnabled();
    fireEvent.click(approve);

    await waitFor(() =>
      expect(decideFactProposal).toHaveBeenCalledWith({
        id: "fact-1",
        decision: "approve",
        reason: "Checked the official company page.",
      }),
    );
  });

  it("explains when the reviewer permission is missing", async () => {
    (fetchFactProposals as jest.Mock).mockRejectedValueOnce(
      Object.assign(new Error("forbidden"), { response: { status: 403 } }),
    );
    renderPage();

    expect(await screen.findByText("صلاحية المراجعة مطلوبة")).toBeInTheDocument();
  });
});
