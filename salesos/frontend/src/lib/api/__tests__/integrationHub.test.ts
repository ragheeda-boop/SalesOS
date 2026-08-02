import {
  createHubConnection,
  listHubConnections,
  testHubConnection,
} from "../integrationHub";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
};

describe("integrationHub API — STORY-08-07", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("lists connections against Hub HTTP path", async () => {
    mocked.get.mockResolvedValue({ data: [{ id: "c1" }] });
    const rows = await listHubConnections("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/integrations/connections",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
    expect(rows).toEqual([{ id: "c1" }]);
  });

  it("creates and tests connections on real endpoints", async () => {
    mocked.post
      .mockResolvedValueOnce({ data: { id: "c2", name: "n" } })
      .mockResolvedValueOnce({
        data: { ok: true, message: "ok", latency_ms: 1 },
      });
    await createHubConnection("tenant-1", {
      connector_key: "fake",
      name: "n",
      credential_ref: "vault:demo/fake",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/integrations/connections",
      expect.objectContaining({ connector_key: "fake" }),
      expect.any(Object),
    );
    const test = await testHubConnection("tenant-1", "c2");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2/test",
      {},
      expect.any(Object),
    );
    expect(test.ok).toBe(true);
  });
});
