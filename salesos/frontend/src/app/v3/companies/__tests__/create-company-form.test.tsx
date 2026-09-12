import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  createCompany: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { createCompany } from "@/lib/api";
import { CreateCompanyForm } from "../create-company-form";

const mockedCreate = createCompany as jest.MockedFunction<typeof createCompany>;

function renderForm(onCancel?: () => void) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreateCompanyForm onCancel={onCancel} />
    </QueryClientProvider>
  );
}

describe("CreateCompanyForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("keeps submit disabled until Arabic name and CR are present", () => {
    renderForm();
    const submit = screen.getByTestId("create-company-submit");
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-company-name-ar"), {
      target: { value: "شركة اختبار" },
    });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByTestId("create-company-cr"), {
      target: { value: "1010000000" },
    });
    expect(submit).not.toBeDisabled();
  });

  it("posts the real createCompany API and stays on /v3/companies/{id}", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "c-new",
      name_ar: "شركة اختبار",
      cr_number: "1010000000",
      status: "active",
      created_at: "2026-09-12",
      updated_at: "2026-09-12",
      name_en: null,
      city: null,
      region: null,
      phone: null,
      email: null,
      confidence_score: null,
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-company-name-ar"), {
      target: { value: "شركة اختبار" },
    });
    fireEvent.change(screen.getByTestId("create-company-cr"), {
      target: { value: "1010000000" },
    });
    fireEvent.click(screen.getByTestId("create-company-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith(
        { name_ar: "شركة اختبار", cr_number: "1010000000" },
        "tenant-1"
      );
    });
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/v3/companies/c-new");
    });
    expect(mockPush).not.toHaveBeenCalledWith("/companies");
  });

  it("shows an honest API error and does not invent a company", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderForm();
    fireEvent.change(screen.getByTestId("create-company-name-ar"), {
      target: { value: "شركة" },
    });
    fireEvent.change(screen.getByTestId("create-company-cr"), {
      target: { value: "1" },
    });
    fireEvent.click(screen.getByTestId("create-company-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create companies."
    );
    expect(mockPush).not.toHaveBeenCalled();
  });
});
