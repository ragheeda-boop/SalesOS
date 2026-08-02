import {
  TIP_OPERATIONAL_FIELDS,
  TIP_SALESOS_AUTHORED_FIELDS,
  tipDefaultConflictRules,
} from "../hubConflictDefaults";

describe("hubConflictDefaults — FE-S08-13", () => {
  it("mirrors tip SalesOS-authored feedback-loop fields", () => {
    expect(TIP_SALESOS_AUTHORED_FIELDS).toContain("risk_score");
    expect(TIP_OPERATIONAL_FIELDS).toContain("cr_number");
  });

  it("builds tip default rules with exclude_from_pull on authored", () => {
    const rules = tipDefaultConflictRules();
    expect(
      rules.some(
        (r) =>
          r.internal === "risk_score" &&
          r.winner === "salesos" &&
          r.exclude_from_pull,
      ),
    ).toBe(true);
    expect(
      rules.some(
        (r) =>
          r.internal === "name" &&
          r.winner === "source" &&
          !r.exclude_from_pull,
      ),
    ).toBe(true);
  });
});
