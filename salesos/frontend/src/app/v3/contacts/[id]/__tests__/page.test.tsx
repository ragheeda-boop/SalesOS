import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@/lib/api", () => ({
  getContact: jest.fn(),
  getCompany: jest.fn(),
  getEntityActivities: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "ct-1" }),
}));

jest.mock("@/components/v3/V3AiPopup", () => ({
  openV3AiPopup: jest.fn(),
}));

import { getContact, getCompany } from "@/lib/api";
import V3Contact360Page from "../page";

const mockedContact = getContact as jest.MockedFunction<typeof getContact>;
const mockedCompany = getCompany as jest.MockedFunction<typeof getCompany>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3Contact360Page />
    </QueryClientProvider>
  );
}

describe("V3 contact detail /contacts leak", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedCompany.mockResolvedValue({
      id: "co-1",
      name_ar: "شركة اختبار",
      name_en: "Test Co",
      cr_number: "1010000000",
      status: "active",
      created_at: "2026-09-12",
      updated_at: "2026-09-12",
      city: null,
      region: null,
      phone: null,
      email: null,
      confidence_score: null,
      branches: [],
      licenses: [],
      contacts: [],
    });
  });

  it("does not leak a loaded contact to legacy /contacts", async () => {
    mockedContact.mockResolvedValue({
      id: "ct-1",
      name: "Ada Contact",
      email: "ada@example.com",
      phone: null,
      position: "Buyer",
      company_id: "co-1",
      company_name: "Test Co",
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Ada Contact" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy contacts/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(document.querySelector('a[href="/v3/contacts"]')).not.toBeNull();
  });

  it("does not leak the company tab to legacy /companies/{id}", async () => {
    mockedContact.mockResolvedValue({
      id: "ct-1",
      name: "Ada Contact",
      email: "ada@example.com",
      phone: null,
      position: "Buyer",
      company_id: "co-1",
      company_name: "Test Co",
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Ada Contact" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Company" }));
    expect(await screen.findByRole("link", { name: "Open Company 360" })).toHaveAttribute(
      "href",
      "/v3/companies/co-1"
    );
    expect(screen.queryByRole("link", { name: /legacy company/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/companies/co-1"]')).toBeNull();
  });

  it("keeps the no-company tab inside v3", async () => {
    mockedContact.mockResolvedValue({
      id: "ct-1",
      name: "No Account",
      email: null,
      phone: null,
      position: null,
      company_id: null,
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "No Account" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Company" }));
    expect(await screen.findByText("No company linked")).toBeInTheDocument();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(screen.queryByRole("link", { name: /legacy contacts/i })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Browse companies" })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
  });
});
