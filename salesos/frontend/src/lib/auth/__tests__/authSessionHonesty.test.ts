import {
  FE_SEC_02_ACCESS_STORAGE,
  FE_SEC_02_HTTPONLY_SLICE,
  FE_SEC_02_PROPOSED_NEXT,
  FE_SEC_02_REFRESH_MITIGATION,
} from "../authSessionHonesty";

describe("authSessionHonesty — FE-SEC-02", () => {
  it("documents dual-path httpOnly slice and LS retention", () => {
    expect(FE_SEC_02_ACCESS_STORAGE).toMatch(/localStorage/);
    expect(FE_SEC_02_ACCESS_STORAGE).toMatch(/Bearer/);
    expect(FE_SEC_02_REFRESH_MITIGATION).toMatch(/httponly/i);
    expect(FE_SEC_02_HTTPONLY_SLICE).toMatch(/salesos_access/);
    expect(FE_SEC_02_HTTPONLY_SLICE).toMatch(/flag OFF/i);
    expect(FE_SEC_02_PROPOSED_NEXT).toMatch(/FLAGS_ON_FIELD_CHECKLIST/);
    expect(FE_SEC_02_PROPOSED_NEXT).toMatch(/verify_token|Bearer/);
  });
});
