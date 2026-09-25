import api from "../client";
import { listCommercialEvidence } from "../evidence";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("listCommercialEvidence", () => {
  it("sends tenant and entity filters through the evidence API", async () => {
    const response = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      read_only: true as const,
    };
    mockApi.get.mockResolvedValueOnce({ data: response });

    await expect(
      listCommercialEvidence("tenant-1", {
        page: 1,
        page_size: 20,
        target_type: "opportunity",
        target_id: "deal-1",
      })
    ).resolves.toEqual(response);
    expect(mockApi.get).toHaveBeenCalledWith("/api/v1/evidence/insights", {
      params: {
        page: 1,
        page_size: 20,
        target_type: "opportunity",
        target_id: "deal-1",
      },
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
