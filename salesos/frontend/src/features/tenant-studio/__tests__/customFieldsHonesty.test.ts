import {
  CUSTOM_FIELDS_AUTO_RENDER_HONESTY,
  CUSTOM_FIELDS_HONESTY,
  CUSTOM_FIELDS_NON_GOALS,
} from "../customFieldsHonesty";

describe("customFieldsHonesty — FE-S10-01/02", () => {
  it("states Preview + in-memory + not Postgres", () => {
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/Preview/i);
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/process memory|in-memory/i);
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/not Postgres/i);
    expect(CUSTOM_FIELDS_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });

  it("auto-render honesty names form-schema + projection-only values", () => {
    expect(CUSTOM_FIELDS_AUTO_RENDER_HONESTY).toMatch(/form-schema|Form Engine/i);
    expect(CUSTOM_FIELDS_AUTO_RENDER_HONESTY).toMatch(/no ORM write/i);
  });
});
