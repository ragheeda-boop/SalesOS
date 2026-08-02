import {
  listNotificationEvents,
  listNotificationRules,
  routeNotificationEvent,
  upsertNotificationRule,
} from "../notificationRulesStudio";

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

describe("notificationRulesStudio API — FE-S10-08", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip events + rules", async () => {
    mocked.get.mockResolvedValueOnce({
      data: { event_types: ["lead.assigned"], channels: ["email"] },
    });
    const events = await listNotificationEvents("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/notification-rules/events",
      expect.any(Object),
    );
    expect(events.event_types).toContain("lead.assigned");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listNotificationRules("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/notification-rules",
      expect.any(Object),
    );
  });

  it("POSTs tip upsert + route", async () => {
    mocked.post.mockResolvedValue({
      data: {
        id: "nr1",
        tenant_id: "t1",
        name: "Alert",
        event_type: "sync.failed",
        channels: ["email"],
        recipients: [{ kind: "owner", value: "self" }],
        conditions: [],
        message_template: "fail",
        priority: 100,
        active: true,
        schema_version: 1,
      },
    });
    await upsertNotificationRule("tenant-1", {
      name: "Alert",
      event_type: "sync.failed",
      channels: ["email"],
      recipients: [{ kind: "owner", value: "self" }],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/notification-rules",
      expect.objectContaining({ name: "Alert" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValue({ data: { matched_rule_ids: ["nr1"] } });
    await routeNotificationEvent("tenant-1", {
      event_type: "sync.failed",
      payload: {},
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/notification-rules/route",
      expect.objectContaining({ event_type: "sync.failed" }),
      expect.any(Object),
    );
  });
});
