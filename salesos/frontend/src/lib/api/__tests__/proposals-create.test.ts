import api from "../client";
import { createProposal } from "../proposals";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createProposal — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/proposals with a null body and query opportunity_id + quote_id", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { id: "p-1", status: "draft", sections: 4 },
    });

    const result = await createProposal("tenant-1", "opp-1", "q-1");

    expect(result.id).toBe("p-1");
    expect(result.status).toBe("draft");
    expect(result.sections).toBe(4);
    expect(mockApi.post).toHaveBeenCalledWith("/api/v1/proposals", null, {
      params: { opportunity_id: "opp-1", quote_id: "q-1" },
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
