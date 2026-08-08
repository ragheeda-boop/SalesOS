/**
 * Proves Sync Gmail / Sync Calendar click handlers fire real API POSTs.
 * Live QA (2026-07-30) reported "no network" — that was likely synthetic-click
 * artifact; this test uses RTL fireEvent on the real buttons.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import client from "@/lib/api/client";
import { GoogleIntegrationPanel } from "../google-panel";

const mockGet = client.get as jest.Mock;
const mockPost = client.post as jest.Mock;

const connectedStatus = {
  connected: true,
  account: {
    id: "acc-1",
    email: "user@example.com",
    provider: "google",
    is_active: true,
    scope: "gmail.readonly calendar.readonly",
    avatar_url: null,
    created_at: "2026-07-28T00:00:00Z",
    last_sync_at: "2026-07-29T19:17:00Z",
    token_expiry: "2026-08-07T00:00:00Z",
  },
  scopes_granted: ["gmail.readonly", "calendar.readonly"],
  token_valid: true,
};

function renderPanel() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <GoogleIntegrationPanel ready={true} hasToken={true} />
    </QueryClientProvider>
  );
}

describe("GoogleIntegrationPanel sync buttons", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGet.mockResolvedValue({ data: connectedStatus });
  });

  it("renders Sync Gmail / Sync Calendar when connected", async () => {
    renderPanel();
    expect(await screen.findByTestId("google-sync-gmail")).toBeInTheDocument();
    expect(screen.getByTestId("google-sync-calendar")).toBeInTheDocument();
  });

  it("Sync Gmail click posts /api/v1/integrations/google/sync", async () => {
    mockPost.mockResolvedValue({
      data: { message: "Synced 3 emails (3 new, 0 updated)", errors: [] },
    });
    renderPanel();
    const btn = await screen.findByTestId("google-sync-gmail");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/integrations/google/sync", {
        days_lookback: 30,
        max_results: 100,
      });
    });
    expect(await screen.findByTestId("google-sync-status")).toHaveTextContent(/Synced 3 emails|Syncing Gmail/);
  });

  it("Sync Calendar click posts /api/v1/integrations/google/calendar-sync", async () => {
    mockPost.mockResolvedValue({
      data: { message: "Synced 2 events (2 new, 0 updated, 0 cancelled)", errors: [] },
    });
    renderPanel();
    const btn = await screen.findByTestId("google-sync-calendar");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/integrations/google/calendar-sync", {
        days_lookback: 90,
        days_forward: 90,
      });
    });
    expect(await screen.findByTestId("google-sync-status")).toHaveTextContent(
      /Synced 2 events|Syncing Calendar/
    );
  });

  it("shows API error detail when sync fails", async () => {
    mockPost.mockRejectedValue({
      response: { data: { detail: "No active Google account" } },
    });
    renderPanel();
    fireEvent.click(await screen.findByTestId("google-sync-gmail"));
    expect(await screen.findByText("No active Google account")).toBeInTheDocument();
  });
});
