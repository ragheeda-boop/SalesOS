import { render, screen } from "@testing-library/react";
import { OwnerOpsPageHonesty } from "../OwnerOpsPageHonesty";

describe("OwnerOpsPageHonesty — FE-S07-07", () => {
  it.each(["flags", "config", "audit"] as const)(
    "renders %s honesty without Production GO claim",
    (surface) => {
      render(<OwnerOpsPageHonesty surface={surface} />);
      const el = screen.getByTestId(`owner-ops-${surface}-honesty`);
      expect(el).toBeInTheDocument();
      expect(el.textContent).toMatch(/Not Production GO/);
      expect(el.textContent).not.toMatch(/Production ready/i);
    }
  );
});
