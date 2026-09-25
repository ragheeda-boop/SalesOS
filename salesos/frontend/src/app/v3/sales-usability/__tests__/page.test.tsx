import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SalesUsabilityPage from "../page";
import {
  fetchSalesUsabilityAccounts,
  fetchSalesUsabilitySummary,
} from "@/lib/reviewQueueQueries";

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true }),
}));

jest.mock("@/lib/reviewQueueQueries", () => ({
  fetchSalesUsabilitySummary: jest.fn(),
  fetchSalesUsabilityAccounts: jest.fn(),
}));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <SalesUsabilityPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.mocked(fetchSalesUsabilitySummary).mockResolvedValue({
    ready_accounts: 43022,
    usable_accounts: 0,
    by_readiness: { SALES_READY: { total: 5710, usable: 0 } },
    by_blocker: { P1_REVIEW_GATE_OPEN: 5710, P2_STRATUM_NOT_ACCEPTED: 37312 },
    gates: { G4: { status: "OPEN", source: "report 90 §1" } },
  });
  jest.mocked(fetchSalesUsabilityAccounts).mockResolvedValue({
    total: 1,
    page: 1,
    page_size: 100,
    items: [
      {
        global_company_id: "gc-1",
        slug: "acme",
        name: "Acme Trading",
        domain: "acme.sa",
        city: "Riyadh",
        sales_readiness: "SALES_READY",
        review_priority: "P1",
        usable: false,
        blockers: ["P1_REVIEW_GATE_OPEN"],
      },
    ],
  });
});

test("renders summary counts, gates, and blocked accounts with reasons", async () => {
  renderPage();
  expect(await screen.findByTestId("ready-count")).toHaveTextContent("43,022");
  expect(screen.getByTestId("usable-count")).toHaveTextContent("0");
  expect(screen.getByText("G4")).toBeInTheDocument();
  expect(await screen.findByText("Acme Trading")).toBeInTheDocument();
  expect(screen.getAllByText(/مراجعة P1 مفتوحة \(G4\)/).length).toBeGreaterThan(0);
});

test("filters send usable and blocker params and reset to page 1", async () => {
  renderPage();
  await screen.findByText("Acme Trading");
  const [statusSelect, blockerSelect] = screen.getAllByRole("combobox");
  fireEvent.change(statusSelect, { target: { value: "blocked" } });
  fireEvent.change(blockerSelect, { target: { value: "PENDING_P3_FUZZY_PAIR" } });
  await waitFor(() =>
    expect(fetchSalesUsabilityAccounts).toHaveBeenLastCalledWith({
      usable: false,
      blocker: "PENDING_P3_FUZZY_PAIR",
      page: 1,
      pageSize: 100,
    }),
  );
});
