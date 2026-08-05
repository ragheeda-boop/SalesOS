import { getBranding, upsertBranding } from "../brandingStudio";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  put: jest.Mock;
};

describe("brandingStudio API — FE-S10-07", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.put.mockReset();
  });

  it("GETs tip branding", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        tenant_id: "tenant-1",
        display_name: "Acme",
        logo_url: "https://cdn.example/logo.png",
        primary_color: "#0F172A",
        secondary_color: "#334155",
        default_locale: "ar",
        supported_locales: ["ar", "en"],
        schema_version: 1,
      },
    });
    const row = await getBranding("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/studio/branding", expect.any(Object));
    expect(row.display_name).toBe("Acme");
  });

  it("PUTs tip branding upsert", async () => {
    mocked.put.mockResolvedValueOnce({
      data: {
        tenant_id: "tenant-1",
        display_name: "Acme AR",
        logo_url: "/assets/logo.svg",
        primary_color: "#112233",
        secondary_color: "#AABBCC",
        default_locale: "en",
        supported_locales: ["en", "ar"],
        schema_version: 1,
      },
    });
    const row = await upsertBranding("tenant-1", {
      display_name: "Acme AR",
      logo_url: "/assets/logo.svg",
      primary_color: "#112233",
      secondary_color: "#AABBCC",
      default_locale: "en",
      supported_locales: ["en", "ar"],
    });
    expect(mocked.put).toHaveBeenCalledWith(
      "/api/v1/studio/branding",
      expect.objectContaining({ display_name: "Acme AR" }),
      expect.any(Object)
    );
    expect(row.primary_color).toBe("#112233");
  });
});
