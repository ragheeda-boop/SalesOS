import { render, screen, fireEvent } from "@testing-library/react";
import { RadioGroup } from "../src/radio-group";

const options = [
  { label: "Option A", value: "a" },
  { label: "Option B", value: "b" },
  { label: "Option C", value: "c" },
];

describe("RadioGroup", () => {
  it("renders all options", () => {
    render(<RadioGroup options={options} />);
    expect(screen.getByText("Option A")).toBeInTheDocument();
    expect(screen.getByText("Option B")).toBeInTheDocument();
    expect(screen.getByText("Option C")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(<RadioGroup label="Choose one" options={options} />);
    expect(screen.getByText("Choose one")).toBeInTheDocument();
  });

  it("calls onChange when option selected", () => {
    const handleChange = jest.fn();
    render(<RadioGroup options={options} onChange={handleChange} />);
    fireEvent.click(screen.getByLabelText("Option B"));
    expect(handleChange).toHaveBeenCalledWith("b");
  });

  it("shows error state", () => {
    render(<RadioGroup options={options} error="Please select" />);
    expect(screen.getByText("Please select")).toBeInTheDocument();
  });

  it("disables all options", () => {
    render(<RadioGroup options={options} disabled />);
    const radios = screen.getAllByRole("radio");
    radios.forEach((radio) => expect(radio).toBeDisabled());
  });

  it("supports horizontal orientation", () => {
    const { container } = render(<RadioGroup options={options} orientation="horizontal" />);
    const group = container.querySelector('[role="radiogroup"]');
    expect(group?.className).toContain("flex-row");
  });
});
