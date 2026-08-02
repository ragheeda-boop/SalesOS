import {
  PERMISSIONS_STUDIO_HONESTY,
  PERMISSIONS_STUDIO_NON_GOALS,
} from "../permissionsStudioHonesty";

describe("permissionsStudioHonesty — FE-S10-06", () => {
  it("states tip HTTP + ceiling + in-memory + not Owner admin roles", () => {
    expect(PERMISSIONS_STUDIO_HONESTY).toMatch(/studio\/permissions/);
    expect(PERMISSIONS_STUDIO_HONESTY).toMatch(/ceiling/i);
    expect(PERMISSIONS_STUDIO_HONESTY).toMatch(/in-memory/i);
    expect(PERMISSIONS_STUDIO_HONESTY).toMatch(/admin\/roles/);
    expect(PERMISSIONS_STUDIO_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });
});
