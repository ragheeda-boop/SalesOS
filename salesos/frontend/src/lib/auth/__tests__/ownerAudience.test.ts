import {
  OWNER_CONSOLE_HOST,
  OWNER_JWT_AUDIENCE,
  TENANT_JWT_AUDIENCE,
  classifyJwtAudience,
  classifyOwnerHost,
  formatOwnerAudienceHonesty,
  formatOwnerHostHonesty,
  getJwtAudience,
  isOwnerConsoleAudience,
} from "../ownerAudience";

function fakeJwt(payload: Record<string, unknown>): string {
  const body = Buffer.from(JSON.stringify(payload), "utf8").toString(
    "base64url",
  );
  return `hdr.${body}.sig`;
}

describe("ownerAudience — STORY-07-03", () => {
  it("classifies owner vs tenant audiences", () => {
    const owner = fakeJwt({ aud: OWNER_JWT_AUDIENCE, sub: "o1" });
    const tenant = fakeJwt({
      aud: TENANT_JWT_AUDIENCE,
      sub: "u1",
      tenant_id: "t1",
    });
    expect(getJwtAudience(owner)).toBe(OWNER_JWT_AUDIENCE);
    expect(classifyJwtAudience(owner)).toBe("owner");
    expect(isOwnerConsoleAudience(owner)).toBe(true);
    expect(classifyJwtAudience(tenant)).toBe("tenant");
    expect(isOwnerConsoleAudience(tenant)).toBe(false);
    expect(classifyJwtAudience(null)).toBe("missing");
  });

  it("formats honest gate copy without claiming Production GO", () => {
    expect(formatOwnerAudienceHonesty("owner")).toContain(OWNER_JWT_AUDIENCE);
    expect(formatOwnerAudienceHonesty("tenant")).toContain("DEC-093");
    expect(formatOwnerAudienceHonesty("tenant")).toContain("Not Production GO");
    expect(formatOwnerAudienceHonesty("missing")).toContain("No access token");
  });

  it("classifies Owner Console host honesty without inventing deploy GO", () => {
    expect(classifyOwnerHost(OWNER_CONSOLE_HOST)).toBe("owner-target");
    expect(classifyOwnerHost("localhost")).toBe("local");
    expect(classifyOwnerHost("app.example.com")).toBe("shared-app");
    expect(formatOwnerHostHonesty("local", "localhost")).toContain(
      OWNER_CONSOLE_HOST,
    );
    expect(formatOwnerHostHonesty("shared-app", "app.example.com")).toContain(
      "Not Production GO",
    );
  });
});
