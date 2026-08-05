import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "../src/sidebar";

describe("Sidebar", () => {
  const sections = [
    {
      items: [
        { icon: <span>H</span>, label: "Home", href: "/" },
        { icon: <span>S</span>, label: "Settings", href: "/settings", badge: 3 },
      ],
    },
  ];

  it("renders all items", () => {
    render(<Sidebar sections={sections} />);
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("shows badge count", () => {
    render(<Sidebar sections={sections} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders toggle button", () => {
    render(<Sidebar sections={sections} />);
    expect(screen.getByRole("button", { name: /collapse/i })).toBeInTheDocument();
  });

  it("calls onToggle when toggle button clicked", () => {
    const onToggle = jest.fn();
    render(<Sidebar sections={sections} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("button", { name: /collapse/i }));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("applies collapsed width", () => {
    const { container } = render(<Sidebar sections={sections} collapsed />);
    expect(container.firstChild).toHaveClass("w-sidebar-collapsed");
  });
});
