import { render, screen, fireEvent } from "@testing-library/react";
import { Checkbox } from "../src/checkbox";

describe("Checkbox", () => {
  it("renders with label", () => {
    render(<Checkbox label="Accept terms" />);
    expect(screen.getByText("Accept terms")).toBeInTheDocument();
  });

  it("calls onChange when clicked", () => {
    const handleChange = jest.fn();
    render(<Checkbox label="Test" onChange={handleChange} />);
    fireEvent.click(screen.getByLabelText("Test"));
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it("shows indeterminate state", () => {
    render(<Checkbox label="Indeterminate" indeterminate />);
    const input = screen.getByRole("checkbox");
    expect(input).toHaveAttribute("aria-checked", "mixed");
  });

  it("shows error state", () => {
    render(<Checkbox label="Error" error errorMessage="Required field" />);
    expect(screen.getByText("Required field")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toHaveAttribute("aria-invalid", "true");
  });

  it("disables when disabled prop is true", () => {
    render(<Checkbox label="Disabled" disabled />);
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });

  it("renders required indicator", () => {
    render(<Checkbox label="Required" required />);
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("supports controlled mode", () => {
    const { rerender } = render(<Checkbox label="Controlled" checked={false} />);
    const input = screen.getByRole("checkbox") as HTMLInputElement;
    expect(input.checked).toBe(false);

    rerender(<Checkbox label="Controlled" checked={true} />);
    expect(input.checked).toBe(true);
  });
});
