import api from "../client";
import { createQuote } from "../quotes";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createQuote — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/quotes with a null body and query opportunity_id + title", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { id: "q-1", title: "Q1", status: "DRAFT", version: 1 },
    });

    const result = await createQuote("tenant-1", "opp-1", "Q1");

    expect(result.id).toBe("q-1");
    expect(result.status).toBe("DRAFT");
    expect(mockApi.post).toHaveBeenCalledWith("/api/v1/quotes", null, {
      params: { opportunity_id: "opp-1", title: "Q1" },
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
