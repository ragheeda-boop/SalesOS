import api from "../client";
import { listAIGovernanceAudit } from "../aiGovernance";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("listAIGovernanceAudit", () => {
  it("requests a tenant-scoped page and returns persisted audit rows", async () => {
    const response = {
      items: [],
      total: 0,
      page: 1,
      page_size: 25,
      generated_at: "2026-09-21T10:00:00+00:00",
      read_only: true as const,
    };
    mockApi.get.mockResolvedValueOnce({ data: response });

    await expect(listAIGovernanceAudit("tenant-1", { page: 1, page_size: 25 })).resolves.toEqual(response);
    expect(mockApi.get).toHaveBeenCalledWith("/api/v1/ai-governance/audit", {
      params: { page: 1, page_size: 25 },
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
