import { render, screen } from "@testing-library/react";
import {
  IntegrationsStudioShell,
  STUDIO_STEPS,
} from "../IntegrationsStudioShell";

describe("IntegrationsStudioShell — STORY-08-07 pointer", () => {
  it("points Owner Console prep to live tenant Studio", () => {
    render(<IntegrationsStudioShell />);
    expect(screen.getByTestId("integrations-studio-shell")).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-api-honesty"),
    ).toHaveTextContent(/Hub HTTP is live/);
    expect(
      screen.getByTestId("integrations-studio-api-honesty"),
    ).toHaveTextContent(/Not Production GO/);
    expect(
      screen.getByTestId("integrations-studio-tenant-link"),
    ).toHaveAttribute("href", "/integrations");
    for (const step of STUDIO_STEPS) {
      expect(
        screen.getByTestId(`integrations-studio-step-${step.id}`),
      ).toHaveAttribute("href", "/integrations");
    }
  });
});
