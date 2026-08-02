import {
  CUSTOM_FIELDS_AUTO_RENDER_HONESTY,
  CUSTOM_FIELDS_HONESTY,
  CUSTOM_FIELDS_NON_GOALS,
} from "../customFieldsHonesty";

describe("customFieldsHonesty — FE-S10-01/02", () => {
  it("states tip HTTP + in-memory + STORY-10-02", () => {
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/custom-fields/);
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/in-memory/i);
    expect(CUSTOM_FIELDS_HONESTY).toMatch(/STORY-10-02/);
    expect(CUSTOM_FIELDS_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });

  it("auto-render honesty names form-schema + projection-only values", () => {
    expect(CUSTOM_FIELDS_AUTO_RENDER_HONESTY).toMatch(/form-schema/);
    expect(CUSTOM_FIELDS_AUTO_RENDER_HONESTY).toMatch(/no ORM write/i);
  });
});
