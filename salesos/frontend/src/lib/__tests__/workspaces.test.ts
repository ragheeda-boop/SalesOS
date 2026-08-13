import {
  getWorkspaceByPath,
  getWorkspaceHome,
  workspaceSelectHref,
  workspaces,
} from "../workspaces";

describe("workspaceSelectHref (REMAINING_GAPS U02)", () => {
  const sales = workspaces.find((w) => w.id === "sales")!;
  const executive = workspaces.find((w) => w.id === "executive")!;

  it("returns the first nav href as workspace home", () => {
    expect(getWorkspaceHome(sales)).toBe("/dashboard");
    expect(getWorkspaceHome(executive)).toBe("/decisions");
  });

  it("does not navigate when the path already belongs to the selected workspace", () => {
    expect(workspaceSelectHref(sales, "/companies")).toBeNull();
    expect(workspaceSelectHref(sales, "/pipeline")).toBeNull();
    expect(workspaceSelectHref(executive, "/decisions")).toBeNull();
  });

  it("navigates to the selected workspace home when leaving another workspace", () => {
    expect(workspaceSelectHref(executive, "/companies")).toBe("/decisions");
    expect(workspaceSelectHref(sales, "/analytics")).toBe("/dashboard");
  });

  it("detects workspace from path", () => {
    expect(getWorkspaceByPath("/gtm/icp").id).toBe("gtm");
    expect(getWorkspaceByPath("/unknown").id).toBe("sales");
  });
});
