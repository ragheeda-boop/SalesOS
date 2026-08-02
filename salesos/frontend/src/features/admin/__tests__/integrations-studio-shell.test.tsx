import { render, screen } from "@testing-library/react";
import {
  IntegrationsStudioShell,
  STUDIO_STEPS,
} from "../IntegrationsStudioShell";

describe("IntegrationsStudioShell — FE-S08-01", () => {
  it("renders disabled Studio steps with API-not-live honesty", () => {
    render(<IntegrationsStudioShell />);
    expect(screen.getByTestId("integrations-studio-shell")).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-api-honesty"),
    ).toHaveTextContent(/Hub HTTP API not live/);
    expect(
      screen.getByTestId("integrations-studio-api-honesty"),
    ).toHaveTextContent(/Not Production GO/);
    for (const step of STUDIO_STEPS) {
      const btn = screen.getByTestId(`integrations-studio-step-${step.id}`);
      expect(btn).toBeDisabled();
      expect(btn).toHaveTextContent(/API not live/i);
    }
  });
});
