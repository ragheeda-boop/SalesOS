import {
  WORKFLOW_STUDIO_HONESTY,
  WORKFLOW_STUDIO_NON_GOALS,
} from "../workflowStudioHonesty";

describe("workflowStudioHonesty — FE-S10-03", () => {
  it("states tip HTTP + WorkflowEngine + for_each deferred", () => {
    expect(WORKFLOW_STUDIO_HONESTY).toMatch(/studio\/workflows/);
    expect(WORKFLOW_STUDIO_HONESTY).toMatch(/WorkflowEngine/);
    expect(WORKFLOW_STUDIO_HONESTY).toMatch(/for_each/);
    expect(WORKFLOW_STUDIO_HONESTY).toMatch(/in-memory/i);
    expect(WORKFLOW_STUDIO_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });
});
