import {
  OWNER_CONSOLE_HOST,
  OWNER_JWT_AUDIENCE,
  TENANT_JWT_AUDIENCE,
  classifyJwtAudience,
  classifyOwnerHost,
  formatOwnerAudienceHonesty,
  formatOwnerAuthDeniedMessage,
  formatOwnerHostHonesty,
  getJwtAudience,
  isAdminApiPath,
  isOwnerConsoleAudience,
  shouldSurfaceOwnerAudienceDenial,
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

  it("keeps tenant and owner audiences distinct (cross-audience FE regression)", () => {
    expect(TENANT_JWT_AUDIENCE).not.toBe(OWNER_JWT_AUDIENCE);
    const owner = fakeJwt({ aud: OWNER_JWT_AUDIENCE, sub: "o2" });
    const tenant = fakeJwt({
      aud: TENANT_JWT_AUDIENCE,
      sub: "u2",
      tenant_id: "t2",
    });
    expect(isOwnerConsoleAudience(owner)).toBe(true);
    expect(isOwnerConsoleAudience(tenant)).toBe(false);
    expect(formatOwnerAudienceHonesty("tenant")).toMatch(/admin/i);
    expect(formatOwnerAudienceHonesty("owner")).not.toMatch(/DEC-093/);
  });

  it("surfaces owner-audience denial for tenant JWT on admin APIs only", () => {
    const tenant = fakeJwt({
      aud: TENANT_JWT_AUDIENCE,
      sub: "u3",
      tenant_id: "t3",
    });
    const owner = fakeJwt({ aud: OWNER_JWT_AUDIENCE, sub: "o3" });
    expect(isAdminApiPath("/api/v1/admin/tenants")).toBe(true);
    expect(isAdminApiPath("/api/v1/identity/login")).toBe(false);
    expect(
      shouldSurfaceOwnerAudienceDenial({
        status: 401,
        url: "/api/v1/admin/billing/dunning",
        token: tenant,
      }),
    ).toBe(true);
    expect(
      shouldSurfaceOwnerAudienceDenial({
        status: 401,
        url: "/api/v1/admin/tenants",
        token: owner,
      }),
    ).toBe(false);
    expect(
      shouldSurfaceOwnerAudienceDenial({
        status: 401,
        url: "/api/v1/identity/me",
        token: tenant,
      }),
    ).toBe(false);
    expect(formatOwnerAuthDeniedMessage("tenant")).toContain("DEC-093");
    expect(formatOwnerAuthDeniedMessage("tenant")).toContain(
      "Tenant session kept",
    );
  });
});
