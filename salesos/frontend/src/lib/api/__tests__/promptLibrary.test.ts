import {
  addPromptLibraryVersion,
  createPromptLibraryEntry,
  deletePromptLibraryEntry,
  getPromptLibraryEntry,
  getPromptLibraryMeta,
  listPromptLibrary,
  rollbackPromptLibrary,
} from "../promptLibrary";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  patch: jest.Mock;
  delete: jest.Mock;
};

describe("promptLibrary API — FE-S12-01", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
    mocked.patch.mockReset();
    mocked.delete.mockReset();
  });

  it("GETs meta/list/detail; POSTs create/version/rollback; DELETEs", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "PromptLibraryEntry",
        capability: "CAP-089",
        extends: "CAP-023",
        operations: ["create", "list"],
        feature_ai_copilot: false,
        honesty: "memory only",
      },
    });
    const meta = await getPromptLibraryMeta("tenant-1");
    expect(meta.feature_ai_copilot).toBe(false);
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/prompt-library/meta",
      expect.any(Object),
    );

    const entry = {
      id: "pl-1",
      tenant_id: "tenant-1",
      name: "Intro",
      key: "gtm.intro.v1",
      active_version: "1.0.0",
      versions: [
        {
          version: "1.0.0",
          template: "hello",
          system: "",
          changelog: "initial",
        },
      ],
      domain: "gtm",
      category: "general",
      schema_version: 1,
      version_count: 1,
    };

    mocked.get.mockResolvedValueOnce({ data: [entry] });
    await listPromptLibrary("tenant-1");

    mocked.get.mockResolvedValueOnce({ data: entry });
    await getPromptLibraryEntry("tenant-1", "pl-1");

    mocked.post.mockResolvedValueOnce({ data: entry });
    await createPromptLibraryEntry("tenant-1", {
      name: "Intro",
      key: "gtm.intro.v1",
      template: "hello",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/prompt-library",
      expect.objectContaining({ key: "gtm.intro.v1" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({
      data: { ...entry, active_version: "1.0.1", version_count: 2 },
    });
    await addPromptLibraryVersion("tenant-1", "pl-1", {
      version: "1.0.1",
      template: "hello2",
      activate: true,
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/prompt-library/pl-1/versions",
      expect.objectContaining({ version: "1.0.1" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({ data: entry });
    await rollbackPromptLibrary("tenant-1", "pl-1", { version: "1.0.0" });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/prompt-library/pl-1/rollback",
      { version: "1.0.0" },
      expect.any(Object),
    );

    mocked.delete.mockResolvedValueOnce({
      data: { deleted: true, id: "pl-1" },
    });
    await deletePromptLibraryEntry("tenant-1", "pl-1");
    expect(mocked.delete).toHaveBeenCalledWith(
      "/api/v1/studio/prompt-library/pl-1",
      expect.any(Object),
    );
  });
});
