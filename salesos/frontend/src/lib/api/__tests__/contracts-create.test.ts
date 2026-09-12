import api from "../client";
import { createContract } from "../contracts";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("createContract — contract", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("POSTs /api/v1/contracts with a JSON body (opportunity_id required)", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { id: "c-1", opportunity_id: "opp-1", status: "DRAFT", title: "" },
    });

    const result = await createContract({ opportunity_id: "opp-1" }, "tenant-1");

    expect(result.id).toBe("c-1");
    expect(result.status).toBe("DRAFT");
    expect(mockApi.post).toHaveBeenCalledWith(
      "/api/v1/contracts",
      { opportunity_id: "opp-1" },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });

  it("forwards optional quote_id and title in the JSON body", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        id: "c-2",
        opportunity_id: "opp-1",
        quote_id: "q-1",
        title: "MSA",
        status: "DRAFT",
      },
    });

    await createContract(
      { opportunity_id: "opp-1", quote_id: "q-1", title: "MSA" },
      "tenant-1"
    );

    expect(mockApi.post).toHaveBeenCalledWith(
      "/api/v1/contracts",
      { opportunity_id: "opp-1", quote_id: "q-1", title: "MSA" },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });
});
