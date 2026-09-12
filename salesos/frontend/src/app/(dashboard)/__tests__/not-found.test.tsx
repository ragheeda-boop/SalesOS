import { render, screen } from "@testing-library/react";
import NotFound from "../not-found";

describe("leftover-layout not-found", () => {
  it("sends leftover 404 users to /v3 instead of leftover /dashboard", () => {
    render(<NotFound />);

    expect(document.querySelector('a[href="/dashboard"]')).toBeNull();
    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/activities"]')).toBeNull();
    expect(document.querySelector('a[href="/tasks"]')).toBeNull();

    expect(screen.getByRole("link", { name: /back to dashboard/i })).toHaveAttribute("href", "/v3");
  });
});
