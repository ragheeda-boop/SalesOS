jest.mock("next/navigation", () => ({
  redirect: jest.fn(),
}));

import { redirect } from "next/navigation";
import V3EmployeeRedirectPage from "../page";

describe("V3EmployeeRedirectPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("stays in v3 and does not exit to /employees/me", () => {
    V3EmployeeRedirectPage();
    expect(redirect).toHaveBeenCalledWith("/v3/people");
    expect(redirect).not.toHaveBeenCalledWith("/employees/me");
  });
});
