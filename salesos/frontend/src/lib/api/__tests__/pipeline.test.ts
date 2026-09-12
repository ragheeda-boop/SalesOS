import api from "../client";
import { createPipeline } from "../pipeline";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createPipeline — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/pipelines with a null body and tenant header", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        id: "pipe-tenant-1",
        name: "Sales Pipeline",
        stages: ["prospecting", "qualification"],
      },
    });

    const result = await createPipeline("tenant-1");

    expect(result.id).toBe("pipe-tenant-1");
    expect(result.name).toBe("Sales Pipeline");
    expect(Array.isArray(result.stages)).toBe(true);
    expect(mockApi.post).toHaveBeenCalledWith("/api/v1/pipelines", null, {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
