import {
  appendAiMemoryTurn,
  deleteAiMemoryConversation,
  getAiMemoryConversation,
  getAiMemoryMeta,
  getAiMemorySettings,
  listAiMemoryConversations,
  probeAiMemoryAdversarial,
  putAiMemorySettings,
} from "../aiMemoryStudio";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

import api from "../client";

const mockedApi = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
  delete: jest.Mock;
};

describe("aiMemoryStudio API — FE-S12-03", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads meta and settings", async () => {
    mockedApi.get
      .mockResolvedValueOnce({
        data: {
          object: "ConversationMemory",
          capability: "CAP-063",
          scope: "conversation",
          cross_session: false,
          opt_in_default: false,
          retention_policy: "conversation",
          provider_cache: "pcm",
          encryption: "fixture-hmac",
          deletion_policy: "DELETE",
          policy_count_delta: 0,
          feature_ai_copilot: false,
          honesty: "no live LLM",
        },
      })
      .mockResolvedValueOnce({
        data: {
          tenant_id: "tenant-1",
          enabled: false,
          max_turns: 50,
          retention_hours: 24,
          opt_in: true,
          cross_session: false,
          feature_ai_copilot: false,
        },
      });

    const meta = await getAiMemoryMeta("tenant-1");
    expect(meta.feature_ai_copilot).toBe(false);
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-memory/meta", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });

    await getAiMemorySettings("tenant-1");
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-memory/settings", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });

  it("wires conversations CRUD + probe", async () => {
    const row = {
      id: "mem-1",
      tenant_id: "tenant-1",
      conversation_id: "c1",
      turns: [{ role: "user", content: "hi" }],
      turn_count: 1,
      provider_cache_key: "pcm:x",
      schema_version: 1,
      scope: "conversation",
    };
    mockedApi.get.mockResolvedValueOnce({ data: [row] }).mockResolvedValueOnce({ data: row });
    mockedApi.put.mockResolvedValueOnce({
      data: {
        tenant_id: "tenant-1",
        enabled: true,
        max_turns: 20,
        retention_hours: 12,
        opt_in: true,
        cross_session: false,
        feature_ai_copilot: false,
      },
    });
    mockedApi.post.mockResolvedValueOnce({ data: row }).mockResolvedValueOnce({
      data: { isolated: true, owner_visible: true, attacker_visible: false },
    });
    mockedApi.delete.mockResolvedValueOnce({
      data: { deleted: true, conversation_id: "c1" },
    });

    await putAiMemorySettings("tenant-1", {
      enabled: true,
      max_turns: 20,
      retention_hours: 12,
    });
    expect(mockedApi.put).toHaveBeenCalledWith(
      "/api/v1/studio/ai-memory/settings",
      { enabled: true, max_turns: 20, retention_hours: 12 },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );

    await listAiMemoryConversations("tenant-1");
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-memory/conversations", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });

    await getAiMemoryConversation("tenant-1", "c1");
    await appendAiMemoryTurn("tenant-1", "c1", {
      role: "user",
      content: "hi",
    });
    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/studio/ai-memory/conversations/c1/turns",
      { role: "user", content: "hi" },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );

    await deleteAiMemoryConversation("tenant-1", "c1");
    expect(mockedApi.delete).toHaveBeenCalledWith("/api/v1/studio/ai-memory/conversations/c1", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });

    await probeAiMemoryAdversarial("tenant-1", {
      owner_tenant_id: "t-a",
      attacker_tenant_id: "t-b",
      conversation_id: "c1",
    });
    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/studio/ai-memory/adversarial/probe",
      {
        owner_tenant_id: "t-a",
        attacker_tenant_id: "t-b",
        conversation_id: "c1",
      },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );
  });
});
