import {
  createHubConnection,
  getActiveHubMapping,
  getHubConnection,
  getHubConflictPolicy,
  listHubConnections,
  putHubConflictPolicy,
  testHubConnection,
  listHubUnlinkedBadges,
} from "../integrationHub";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
};

describe("integrationHub API — STORY-08-07 / FE-S08-08/09", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
    mocked.put.mockReset();
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

  it("gets and puts conflict-policy on tip Hub HTTP", async () => {
    mocked.get.mockResolvedValue({
      data: {
        id: "p1",
        connection_id: "c2",
        rules: [],
        salesos_authored_fields: ["risk_score"],
        operational_fields: ["name"],
      },
    });
    mocked.put.mockResolvedValue({
      data: {
        id: "p1",
        connection_id: "c2",
        rules: [{ internal: "name", winner: "source" }],
        salesos_authored_fields: ["risk_score"],
        operational_fields: ["name"],
      },
    });
    const got = await getHubConflictPolicy("tenant-1", "c2");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2/conflict-policy",
      expect.any(Object),
    );
    expect(got.salesos_authored_fields).toContain("risk_score");
    const put = await putHubConflictPolicy("tenant-1", "c2", {
      rules: [{ internal: "name", winner: "source" }],
      salesos_authored_fields: ["risk_score"],
      operational_fields: ["name"],
    });
    expect(mocked.put).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2/conflict-policy",
      expect.objectContaining({ rules: expect.any(Array) }),
      expect.any(Object),
    );
    expect(put.rules[0].internal).toBe("name");
  });

  it("loads active mapping against tip Hub HTTP", async () => {
    mocked.get.mockResolvedValue({
      data: {
        id: "m1",
        connection_id: "c2",
        model: "company",
        version: 1,
        mappings: [{ external: "name", internal: "name" }],
        baseline_fields: [],
        is_active: true,
      },
    });
    const row = await getActiveHubMapping("tenant-1", "c2", "company");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2/mappings/active",
      expect.objectContaining({
        params: { model: "company" },
      }),
    );
    expect(row?.model).toBe("company");
  });

  it("getHubConnection fetches one connection", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        id: "c2",
        tenant_id: "t1",
        connector_key: "fake",
        name: "Demo",
        credential_ref: "vault:x",
        connection_config: {},
        cursor_state: {},
        is_active: true,
      },
    });
    const row = await getHubConnection("tenant-1", "c2");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2",
      expect.any(Object),
    );
    expect(row.id).toBe("c2");
  });
  it("lists unlinked badges on tip Hub HTTP (STORY-09-08)", async () => {
    mocked.get.mockResolvedValue({
      data: {
        connection_id: "c2",
        count: 1,
        items: [
          {
            kind: "unlinked_badge",
            external_id: "p1",
            status: "unlinked",
            cr_number: "123",
            message: "no match",
          },
        ],
      },
    });
    const row = await listHubUnlinkedBadges("tenant-1", "c2");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/integrations/connections/c2/unlinked-badges",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
        params: { limit: 100, sync_run_limit: 50 },
      }),
    );
    expect(row.count).toBe(1);
    expect(row.items[0].status).toBe("unlinked");
  });
});
