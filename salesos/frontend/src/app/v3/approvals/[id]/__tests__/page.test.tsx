import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "approval-1" }),
  useRouter: () => ({ push: jest.fn() }),
}));

import apiClient from "@/lib/api/client";
import V3ApprovalDetailPage from "../page";

const mockedGet = apiClient.get as jest.MockedFunction<typeof apiClient.get>;
const mockedPost = apiClient.post as jest.MockedFunction<typeof apiClient.post>;

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <V3ApprovalDetailPage />
    </QueryClientProvider>
  );
}

describe("V3ApprovalDetailPage decide", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGet.mockResolvedValue({
      data: { id: "approval-1", status: "PENDING", action_summary: "Review request" },
    } as never);
    mockedPost.mockResolvedValue({ data: {} } as never);
  });

  it("does not send a client-chosen decided_by", async () => {
    renderPage();

    fireEvent.click(await screen.findByRole("button", { name: /Approve/ }));

    await waitFor(() => expect(mockedPost).toHaveBeenCalledTimes(1));
    const [url, body, config] = mockedPost.mock.calls[0];

    expect(url).toBe("/api/v1/approvals/approval-1/decide");
    expect(body).toEqual({ decision: "APPROVED", authority_level: "MANAGER" });
    expect(body).not.toHaveProperty("decided_by");
    expect(config).toEqual({ headers: { "X-Tenant-Id": "tenant-1" } });
  });
});
