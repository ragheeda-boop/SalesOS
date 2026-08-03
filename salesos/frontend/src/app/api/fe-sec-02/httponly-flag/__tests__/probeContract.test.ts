/**
 * FE-SEC-02 #5 bake probe route — shape only (env default OFF).
 */
/** Mirrors route JSON contract without importing Next server bits in Jest. */
function buildProbePayload(env: {
  NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE?: string;
  FEATURE_HTTPONLY_ACCESS_COOKIE?: string;
}) {
  const nextPublicRaw =
    env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE ?? null;
  return {
    feature: "FE-SEC-02",
    next_public_httponly_access_cookie_baked: nextPublicRaw === "true",
    next_public_raw: nextPublicRaw,
    server_feature_httponly_access_cookie:
      env.FEATURE_HTTPONLY_ACCESS_COOKIE === "true",
  };
}

describe("FE-SEC-02 httponly-flag probe contract", () => {
  it("defaults baked=false when NEXT_PUBLIC unset", () => {
    const payload = buildProbePayload({});
    expect(payload.next_public_httponly_access_cookie_baked).toBe(false);
    expect(payload.server_feature_httponly_access_cookie).toBe(false);
  });

  it("reports baked=true only for exact NEXT_PUBLIC true", () => {
    expect(
      buildProbePayload({
        NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE: "true",
      }).next_public_httponly_access_cookie_baked,
    ).toBe(true);
    expect(
      buildProbePayload({
        NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE: "false",
      }).next_public_httponly_access_cookie_baked,
    ).toBe(false);
  });
});
