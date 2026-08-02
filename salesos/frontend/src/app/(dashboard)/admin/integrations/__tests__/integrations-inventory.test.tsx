import { render, screen } from "@testing-library/react";
import AdminIntegrationsInventoryPage from "../page";

describe("AdminIntegrationsInventoryPage — FE-S08-00", () => {
  it("renders honesty stub without claiming Hub HTTP or Production GO", () => {
    render(<AdminIntegrationsInventoryPage />);
    expect(screen.getByTestId("admin-integrations-page")).toBeInTheDocument();
    expect(
      screen.getByTestId("owner-ops-integrations-honesty"),
    ).toHaveTextContent(/Not Production GO/);
    expect(
      screen.getByTestId("admin-integrations-be-landed"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("admin-integrations-item-STORY-08-01"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("admin-integrations-item-STORY-08-07"),
    ).toHaveTextContent(/blocked/i);
    expect(
      screen.getByTestId("admin-integrations-overview-link"),
    ).toHaveAttribute("href", "/admin");
  });
});
