import { render, screen } from "@testing-library/react";
import AdminIntegrationsInventoryPage from "../page";

describe("AdminIntegrationsInventoryPage — FE-S08-00/01 + STORY-08-07", () => {
  it("renders inventory + Studio pointer to live Hub HTTP tenant flow", () => {
    render(<AdminIntegrationsInventoryPage />);
    expect(screen.getByTestId("admin-integrations-page")).toBeInTheDocument();
    expect(screen.getByTestId("owner-ops-integrations-honesty")).toHaveTextContent(
      /Not Production GO/
    );
    expect(screen.getByTestId("integrations-studio-shell")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-studio-api-honesty")).toHaveTextContent(
      /Hub HTTP is live/i
    );
    expect(screen.getByTestId("admin-integrations-be-landed")).toBeInTheDocument();
    expect(screen.getByTestId("admin-integrations-item-STORY-08-01")).toBeInTheDocument();
    expect(screen.getByTestId("admin-integrations-item-STORY-08-07")).toHaveTextContent(/landed/i);
    expect(screen.getByTestId("admin-integrations-overview-link")).toHaveAttribute(
      "href",
      "/admin"
    );
  });
});
