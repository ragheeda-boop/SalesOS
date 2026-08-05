import {
  compileWorkflowCanvas,
  compileWorkflowCanvasEphemeral,
  listWorkflowCanvases,
  upsertWorkflowCanvas,
} from "../workflowStudio";

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

describe("workflowStudio API — FE-S10-03", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip workflow canvases", async () => {
    mocked.get.mockResolvedValue({ data: [] });
    await listWorkflowCanvases("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/workflows",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      })
    );
  });

  it("POSTs tip canvas upsert", async () => {
    mocked.post.mockResolvedValue({
      data: {
        id: "c1",
        tenant_id: "t1",
        name: "Demo",
        description: "",
        trigger_type: "manual",
        nodes: [],
        schema_version: 1,
      },
    });
    const row = await upsertWorkflowCanvas("tenant-1", {
      name: "Demo",
      nodes: [{ id: "n1", kind: "action", step_type: "log_message", config: {} }],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/workflows",
      expect.objectContaining({ name: "Demo" }),
      expect.any(Object)
    );
    expect(row.id).toBe("c1");
  });

  it("POSTs tip compile for saved and ephemeral", async () => {
    mocked.post.mockResolvedValue({
      data: { canvas_id: "c1", workflow: { steps: [] } },
    });
    await compileWorkflowCanvas("tenant-1", "c1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/workflows/c1/compile",
      {},
      expect.any(Object)
    );

    mocked.post.mockResolvedValue({ data: { workflow: { steps: [] } } });
    await compileWorkflowCanvasEphemeral("tenant-1", {
      name: "tmp",
      nodes: [],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/workflows/compile",
      expect.objectContaining({ name: "tmp" }),
      expect.any(Object)
    );
  });
});
