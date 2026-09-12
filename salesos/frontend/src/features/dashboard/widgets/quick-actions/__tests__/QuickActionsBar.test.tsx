import { render, screen } from "@testing-library/react";

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

import { QuickActionsBar } from "../QuickActionsBar";

describe("leftover dashboard QuickActionsBar golden-path hubs", () => {
  it("retargets leftover hub dumps to v3 and does not leak listed leftover hubs", () => {
    render(<QuickActionsBar />);

    expect(document.querySelector('a[href="/companies"]')).toBeNull();
    expect(document.querySelector('a[href="/companies/new"]')).toBeNull();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(document.querySelector('a[href="/opportunities"]')).toBeNull();
    expect(document.querySelector('a[href="/activities"]')).toBeNull();
    expect(document.querySelector('a[href="/tasks"]')).toBeNull();
    expect(document.querySelector('a[href="/dashboard"]')).toBeNull();

    expect(screen.getByRole("link", { name: /dashboard\.new_company/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
    expect(screen.getByRole("link", { name: "الصفقات" })).toHaveAttribute("href", "/v3/crm");
    expect(screen.getByRole("link", { name: "الأنشطة" })).toHaveAttribute("href", "/v3/activities");
  });
});
