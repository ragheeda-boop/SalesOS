import { createElement } from "react";
import { render, screen } from "@testing-library/react";
import { TenantBrandMark } from "../TenantBrandMark";

jest.mock("@/lib/hooks/brandingStudioQueries", () => ({
  useBranding: jest.fn(),
}));

import { useBranding } from "@/lib/hooks/brandingStudioQueries";

const mockedUseBranding = useBranding as jest.Mock;

describe("TenantBrandMark — FE-S10-07b", () => {
  beforeEach(() => {
    mockedUseBranding.mockReset();
  });

  it("falls back to SalesOS when tip branding empty", () => {
    mockedUseBranding.mockReturnValue({
      data: {
        tenant_id: "t1",
        display_name: "",
        logo_url: "",
        primary_color: "#0F172A",
        secondary_color: "#334155",
        default_locale: "ar",
        supported_locales: ["ar", "en"],
        schema_version: 1,
      },
      isLoading: false,
      isError: false,
    });
    render(createElement(TenantBrandMark));
    expect(screen.getByTestId("tenant-brand-name").textContent).toBe("SalesOS");
    expect(screen.getByTestId("tenant-brand-swatch")).toBeTruthy();
  });

  it("renders tip display_name", () => {
    mockedUseBranding.mockReturnValue({
      data: {
        tenant_id: "t1",
        display_name: "Acme Tenant",
        logo_url: "https://cdn.example/logo.png",
        primary_color: "#112233",
        secondary_color: "#445566",
        default_locale: "en",
        supported_locales: ["en"],
        schema_version: 1,
      },
      isLoading: false,
      isError: false,
    });
    render(createElement(TenantBrandMark));
    expect(screen.getByTestId("tenant-brand-name").textContent).toBe(
      "Acme Tenant",
    );
  });
});
