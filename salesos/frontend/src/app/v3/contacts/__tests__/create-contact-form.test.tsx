import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  createContact: jest.fn(),
  searchCompanies: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { createContact, searchCompanies } from "@/lib/api";
import { CreateContactForm } from "../create-contact-form";

const mockedCreate = createContact as jest.MockedFunction<typeof createContact>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;

function renderForm(onCancel?: () => void) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateContactForm onCancel={onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateContactForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedCompanies.mockResolvedValue({
      items: [
        {
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
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    });
  });

  it("keeps submit disabled until name and company_id are present", async () => {
    renderForm();
    const submit = await screen.findByTestId("create-contact-submit");
    expect(submit).toBeDisabled();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-contact-name"), {
      target: { value: "نورة" },
    });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-contact-company"), {
      target: { value: "co-1" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts the real createContact API and stays on /v3/contacts/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "ct-new",
      name: "نورة",
      email: "n@test.com",
      phone: null,
      position: "مديرة",
      company_id: "co-1",
    });
    renderForm();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-contact-name"), {
      target: { value: "نورة" },
    });
    fireEvent.change(screen.getByTestId("create-contact-company"), {
      target: { value: "co-1" },
    });
    fireEvent.change(screen.getByTestId("create-contact-email"), {
      target: { value: "n@test.com" },
    });
    fireEvent.click(screen.getByTestId("create-contact-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith(
        { name: "نورة", company_id: "co-1", email: "n@test.com" },
        "tenant-1"
      );
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/contacts/ct-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/contacts");
  });

  it("shows an honest API error and does not invent a contact", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    await screen.findByRole("option", { name: "Test Co" });
    fireEvent.change(screen.getByTestId("create-contact-name"), {
      target: { value: "نورة" },
    });
    fireEvent.change(screen.getByTestId("create-contact-company"), {
      target: { value: "co-1" },
    });
    fireEvent.click(screen.getByTestId("create-contact-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create contacts."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("points to /v3/companies when no company_id options exist", async () => {
    mockedCompanies.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });
    renderForm();
    expect(await screen.findByTestId("create-contact-no-companies")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create company/i })).toHaveAttribute(
      "href",
      "/v3/companies"
    );
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(screen.getByTestId("create-contact-submit")).toBeDisabled();
  });
});
