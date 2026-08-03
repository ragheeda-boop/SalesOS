import {
  FE_SEC_02_ACCESS_STORAGE,
  FE_SEC_02_PROPOSED_NEXT,
  FE_SEC_02_REFRESH_MITIGATION,
} from "../authSessionHonesty";

describe("authSessionHonesty — FE-SEC-02", () => {
  it("documents access LS retention and cookie-first refresh", () => {
    expect(FE_SEC_02_ACCESS_STORAGE).toMatch(/localStorage/);
    expect(FE_SEC_02_ACCESS_STORAGE).toMatch(/middleware/);
    expect(FE_SEC_02_REFRESH_MITIGATION).toMatch(/httponly/i);
    expect(FE_SEC_02_PROPOSED_NEXT).toMatch(/BFF/);
  });
});
