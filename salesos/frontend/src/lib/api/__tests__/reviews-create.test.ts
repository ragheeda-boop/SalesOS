import api from "../client";
import { createReview } from "../reviews";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createReview — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/reviews with a null body and query review_type + target_id + target_type", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { id: "rev-1", status: "pending", review_type: "deal_review" },
    });

    const result = await createReview("tenant-1", "deal_review", "opp-1", "opportunity");

    expect(result.id).toBe("rev-1");
    expect(result.status).toBe("pending");
    expect(result.review_type).toBe("deal_review");
    expect(mockApi.post).toHaveBeenCalledWith("/api/v1/reviews", null, {
      params: {
        review_type: "deal_review",
        target_id: "opp-1",
        target_type: "opportunity",
        assigned_to: "",
      },
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
