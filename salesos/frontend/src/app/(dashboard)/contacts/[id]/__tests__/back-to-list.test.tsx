import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "ct-1" }),
  useRouter: () => ({ push }),
}));

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  useTenant: () => ({ tenantId: "tenant-1" }),
}));

const apiGet = jest.fn();
jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => apiGet(...args),
    delete: jest.fn(),
  },
}));

import LeftoverContactPage from "../page";

describe("leftover contact 360 back-to-list", () => {
  beforeEach(() => {
    push.mockReset();
    apiGet.mockReset();
  });

  it("retargets leftover contact list breadcrumb to /v3/contacts", async () => {
    apiGet.mockImplementation((url: string) => {
      if (url === "/api/v1/contacts/ct-1") {
        return Promise.resolve({
          data: { id: "ct-1", name: "Ada Contact", company_id: null },
        });
      }
      return Promise.resolve({ data: { items: [] } });
    });

    render(<LeftoverContactPage />);

    expect(await screen.findByRole("heading", { name: "Ada Contact" })).toBeInTheDocument();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(screen.getByRole("link", { name: "nav.contacts" })).toHaveAttribute("href", "/v3/contacts");
  });

  it("sends leftover contact empty-state back-to-list to /v3/contacts", async () => {
    apiGet.mockRejectedValue(new Error("missing"));

    render(<LeftoverContactPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "العودة للقائمة" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "العودة للقائمة" }));
    expect(push).toHaveBeenCalledWith("/v3/contacts");
    expect(push).not.toHaveBeenCalledWith("/contacts");
  });
});
