import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: () => ({ ready: true, hasToken: true, audienceKind: "salesos-api" }),
}));

jest.mock("@salesos/hooks", () => ({
  useDebounce: (value: string) => value,
}));

jest.mock("@/lib/api", () => ({
  searchContacts: jest.fn(),
  createContact: jest.fn(),
  searchCompanies: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

import { searchContacts, searchCompanies } from "@/lib/api";
import V3ContactsPage from "../page";

const mockedSearch = searchContacts as jest.MockedFunction<typeof searchContacts>;
const mockedCompanies = searchCompanies as jest.MockedFunction<typeof searchCompanies>;

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <V3ContactsPage />
    </QueryClientProvider>
  );
}

describe("V3ContactsPage empty / create hole", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedSearch.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 });
    mockedCompanies.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 });
  });

  it("does not leak an empty tenant to legacy /contacts", async () => {
    renderPage();
    expect(await screen.findByText("No contacts found")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /legacy contacts/i })).not.toBeInTheDocument();
    expect(document.querySelector('a[href="/contacts"]')).toBeNull();
    expect(screen.getByTestId("contacts-empty-create")).toBeInTheDocument();
  });

  it("opens the in-v3 create form from the empty state", async () => {
    renderPage();
    fireEvent.click(await screen.findByTestId("contacts-empty-create"));
    await waitFor(() => {
      expect(screen.getByTestId("create-contact-submit")).toBeInTheDocument();
    });
  });
});
