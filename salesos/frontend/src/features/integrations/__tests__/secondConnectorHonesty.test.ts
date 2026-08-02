import {
  SECOND_CONNECTOR_HONESTY,
  SECOND_CONNECTOR_NON_GOALS,
} from "../secondConnectorHonesty";

describe("secondConnectorHonesty — FE-S11-10", () => {
  it("states tip certify HTTP + hubspot + no live network claim", () => {
    expect(SECOND_CONNECTOR_HONESTY).toMatch(/certify/);
    expect(SECOND_CONNECTOR_HONESTY).toMatch(/hubspot/i);
    expect(SECOND_CONNECTOR_HONESTY).toMatch(/not claimed/i);
    expect(SECOND_CONNECTOR_NON_GOALS.join(" ")).toMatch(
      /pilot|OAuth|network/i,
    );
  });
});
