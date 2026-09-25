import { resolvePostLoginPath } from "../loginRedirect";

const ORIGIN = "http://localhost:3000";

describe("resolvePostLoginPath", () => {
  it("preserves the protected destination emitted by middleware", () => {
    const search = new URLSearchParams("callbackUrl=%2Fv3%2Ffact-review%3Fstatus%3DPROPOSED");
    expect(resolvePostLoginPath(search, ORIGIN)).toBe("/v3/fact-review?status=PROPOSED");
  });

  it("continues to support the legacy next parameter", () => {
    expect(resolvePostLoginPath(new URLSearchParams("next=%2Fv3%2Fcompanies"), ORIGIN)).toBe(
      "/v3/companies"
    );
  });

  it("prefers callbackUrl when both parameters are present", () => {
    const search = new URLSearchParams("callbackUrl=%2Fv3%2Ffact-review&next=%2Fv3");
    expect(resolvePostLoginPath(search, ORIGIN)).toBe("/v3/fact-review");
  });

  it.each([
    "https://attacker.example/path",
    "//attacker.example/path",
    "/\\attacker.example/path",
    "relative/path",
  ])("falls back for an unsafe destination: %s", (candidate) => {
    const search = new URLSearchParams({ callbackUrl: candidate });
    expect(resolvePostLoginPath(search, ORIGIN)).toBe("/v3");
  });

  it("falls back when no destination is supplied", () => {
    expect(resolvePostLoginPath(new URLSearchParams(), ORIGIN)).toBe("/v3");
  });
});
