import {
  NOTIFICATION_RULES_HONESTY,
  NOTIFICATION_RULES_NON_GOALS,
} from "../notificationRulesHonesty";

describe("notificationRulesHonesty — FE-S10-08", () => {
  it("states tip HTTP + RulesEngine + in-memory", () => {
    expect(NOTIFICATION_RULES_HONESTY).toMatch(/notification-rules/);
    expect(NOTIFICATION_RULES_HONESTY).toMatch(/RulesEngine/);
    expect(NOTIFICATION_RULES_HONESTY).toMatch(/in-memory/i);
    expect(NOTIFICATION_RULES_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });
});
