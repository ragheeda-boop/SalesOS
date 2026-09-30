import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
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
  useParams: () => ({ id: "rev-1" }),
  useRouter: () => ({ push: jest.fn() }),
}));

import apiClient from "@/lib/api/client";
import V3ReviewDetailPage from "../[id]/page";

const mockedGet = apiClient.get as jest.MockedFunction<typeof apiClient.get>;
const mockedPost = apiClient.post as jest.MockedFunction<typeof apiClient.post>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3ReviewDetailPage />
    </QueryClientProvider>
  );
}

describe("V3ReviewDetailPage decide", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGet.mockResolvedValue({
      data: { id: "rev-1", status: "in_progress", review_type: "deal_review" },
    } as never);
    mockedPost.mockResolvedValue({ data: {} } as never);
  });

  it("does not send a client-chosen decided_by", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Approve/ }));
    await waitFor(() => expect(mockedPost).toHaveBeenCalledTimes(1));
    const url = mockedPost.mock.calls[0][0] as string;
    expect(url).toBe("/api/v1/reviews/rev-1/decide?decision=approve&comments=");
    expect(url).not.toContain("decided_by");
  });
});
