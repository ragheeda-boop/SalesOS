import {
  DEFAULT_TASK_MAPPINGS,
  TASK_CASE_TYPES,
  TASK_FINANCING_FIELDS,
  isTaskModel,
} from "../odooTaskHonesty";

describe("odooTaskHonesty — FE-S09-05", () => {
  it("mirrors tip project.task mapping preset", () => {
    expect(isTaskModel("project.task")).toBe(true);
    expect(isTaskModel("helpdesk.ticket")).toBe(false);
    expect(
      DEFAULT_TASK_MAPPINGS.some(
        (m) => m.external === "stage_id" && m.internal === "stage",
      ),
    ).toBe(true);
  });

  it("exposes TaskCaseExtension VO case types (not aggregate)", () => {
    expect(TASK_CASE_TYPES).toEqual(
      expect.arrayContaining(["financing", "insurance", "generic"]),
    );
    expect(TASK_FINANCING_FIELDS[0]).toContain("financing");
  });
});
