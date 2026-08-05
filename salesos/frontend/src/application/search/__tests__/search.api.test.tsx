jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}));

import api from "@/lib/api";
import { searchApi, suggestApi } from "../search.api";

const mockedApi = api as jest.Mocked<typeof api>;

describe("searchApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("makes a GET request and returns JSON", async () => {
    const response = { results: [], total: 0 };
    mockedApi.get.mockResolvedValue({ data: response } as any);

    const result = await searchApi({
      text: "test",
      filters: [],
      page: 1,
      pageSize: 10,
    });

    expect(result).toEqual(response);
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/search", {
      params: {
        q: "test",
        strategy: "hybrid",
        limit: 10,
        offset: 0,
        include_facets: true,
        city: undefined,
        region: undefined,
        industry: undefined,
        status: undefined,
      },
    });
  });

  it("propagates API errors", async () => {
    mockedApi.get.mockRejectedValue(new Error("Network Error"));

    await expect(searchApi({ text: "test", filters: [], page: 1, pageSize: 10 })).rejects.toThrow(
      "Network Error"
    );
  });
});

describe("suggestApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns suggestions", async () => {
    const suggestions = [{ id: "1", type: "company", score: 0.9, data: { name: "Acme" } }];
    mockedApi.get.mockResolvedValue({
      data: { suggestions },
    } as any);

    const result = await suggestApi("acme");

    expect(result).toEqual(suggestions);
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/search/suggest", {
      params: { q: "acme", limit: 5 },
    });
  });

  it("returns empty array when suggestions are missing", async () => {
    mockedApi.get.mockResolvedValue({ data: {} } as any);

    const result = await suggestApi("acme");

    expect(result).toEqual([]);
  });
});
