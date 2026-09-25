import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";
import { decideFactProposal, fetchFactProposals } from "../factReviewQueries";

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: jest.fn(() => "tenant-42"),
}));

const mockedApi = apiClient as jest.Mocked<typeof apiClient>;

describe("fact review API client", () => {
  beforeEach(() => jest.clearAllMocks());

  it("fetches a status page with tenant scope", async () => {
    const payload = { items: [], limit: 50, offset: 0 };
    mockedApi.get.mockResolvedValueOnce({ data: payload } as never);

    await expect(
      fetchFactProposals({ status: "PROPOSED", limit: 50, offset: 0 }),
    ).resolves.toEqual(payload);
    expect(getTenantId).toHaveBeenCalled();
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/facts/proposals", {
      params: { status: "PROPOSED", limit: 50, offset: 0 },
      headers: { "X-Tenant-Id": "tenant-42" },
    });
  });

  it("posts the decision and reason to the fact endpoint", async () => {
    const payload = {
      id: "fact-1",
      status: "APPROVED" as const,
      reviewed_at: "2026-09-21T12:00:00Z",
      changed: true,
      crm_applied: false as const,
    };
    mockedApi.post.mockResolvedValueOnce({ data: payload } as never);

    await expect(
      decideFactProposal({
        id: "fact/1",
        decision: "approve",
        reason: "Confirmed against the source.",
      }),
    ).resolves.toEqual(payload);
    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/facts/fact%2F1/decision",
      { decision: "approve", reason: "Confirmed against the source." },
      { headers: { "X-Tenant-Id": "tenant-42" } },
    );
  });
});
