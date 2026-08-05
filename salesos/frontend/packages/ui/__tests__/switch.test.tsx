import { render, screen, fireEvent } from "@testing-library/react";
import { Switch } from "../src/switch";

describe("Switch", () => {
  it("renders with label", () => {
    render(<Switch label="Enable notifications" />);
    expect(screen.getByText("Enable notifications")).toBeInTheDocument();
  });

  it('has role="switch"', () => {
    render(<Switch label="Test" />);
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  it("toggles on click", () => {
    const handleChange = jest.fn();
    render(<Switch label="Toggle" onChange={handleChange} />);
    fireEvent.click(screen.getByRole("switch"));
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it("disables when disabled prop is true", () => {
    render(<Switch label="Disabled" disabled />);
    expect(screen.getByRole("switch")).toBeDisabled();
  });

  it("supports controlled mode", () => {
    const { rerender } = render(<Switch label="Controlled" checked={false} />);
    const sw = screen.getByRole("switch");
    expect(sw).toHaveAttribute("aria-checked", "false");

    rerender(<Switch label="Controlled" checked={true} />);
    expect(sw).toHaveAttribute("aria-checked", "true");
  });
});
