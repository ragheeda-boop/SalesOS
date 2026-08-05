import { render, screen } from "@testing-library/react";

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn(),
    replace: jest.fn(),
  }),
}));

jest.mock("next/link", () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

jest.mock("@salesos/ui", () => {
  const actual = jest.requireActual("@salesos/ui");
  return {
    ...actual,
    Avatar: ({ fallback, size: _size, className, ..._props }: any) => (
      <span className={className} data-testid="avatar" aria-hidden="true">
        {fallback}
      </span>
    ),
  };
});

import { DealCard } from "../PipelineWorkspace";

function makeOpp(overrides: Record<string, unknown> = {}) {
  return {
    id: "opp-1",
    name: "Test Deal",
    value: 500000,
    stage: "lead",
    status: "open",
    company_name: "Acme Corp",
    company_id: "comp-1",
    owner_id: "owner-1",
    expected_close_date: "2026-08-01",
    ...overrides,
  };
}

describe("DealCard", () => {
  it("renders deal name", () => {
    render(<DealCard opportunity={makeOpp()} />);
    expect(screen.getByText("Test Deal")).toBeInTheDocument();
  });

  it("links company name to company page", () => {
    render(<DealCard opportunity={makeOpp()} />);
    const link = screen.getByText("Acme Corp");
    expect(link.closest("a")).toHaveAttribute("href", "/companies/comp-1");
  });

  it("shows formatted deal value in SAR", () => {
    render(<DealCard opportunity={makeOpp({ value: 2500000 })} />);
    expect(screen.getByText(/2\.5M SAR/)).toBeInTheDocument();
  });

  it("shows owner avatar with initials fallback", () => {
    render(<DealCard opportunity={makeOpp()} />);
    const avatar = screen.getByTestId("avatar");
    expect(avatar).toBeInTheDocument();
  });

  it("shows deal age from expected_close_date", () => {
    render(<DealCard opportunity={makeOpp({ expected_close_date: "2026-06-01" })} />);
    expect(screen.getByText(/\d+d/)).toBeInTheDocument();
  });

  it("renders score badge when healthScore provided", () => {
    render(<DealCard opportunity={makeOpp()} healthScore={92} />);
    expect(screen.getByText("92")).toBeInTheDocument();
  });

  it("renders score badge with fallback when healthScore missing", () => {
    render(<DealCard opportunity={makeOpp()} />);
    // Missing healthScore renders an em-dash placeholder (not a rounded Badge).
    // Age may also render "—" when expected_close_date is null — accept ≥1.
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("renders GripVertical drag handle", () => {
    const { container } = render(<DealCard opportunity={makeOpp()} />);
    const svg = container.querySelector("svg.lucide-grip-vertical");
    expect(svg).not.toBeNull();
  });
});
