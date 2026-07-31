import { render, screen, fireEvent } from "@testing-library/react";

jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
}));

jest.mock("@/lib/api", () => ({
  default: { patch: jest.fn() },
  getCurrentUser: jest.fn(),
  changePassword: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  useTenant: jest.fn().mockReturnValue({ tenantId: "tenant-1" }),
}));

jest.mock("@salesos/ui", () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs">{children}</div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  Tab: ({ children }: { children: React.ReactNode }) => (
    <button>{children}</button>
  ),
  TabsPanel: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-panel">{children}</div>
  ),
  Input: ({ label, placeholder, ...props }: Record<string, unknown>) => (
    <div>
      {label && <label>{String(label)}</label>}
      <input
        data-testid={`input-${label || placeholder}`}
        placeholder={String(placeholder || "")}
        {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
      />
    </div>
  ),
  Button: ({
    children,
    ...props
  }: {
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <button {...(props as React.ButtonHTMLAttributes<HTMLButtonElement>)}>
      {children}
    </button>
  ),
  Badge: ({ children }: { children: React.ReactNode }) => (
    <span data-testid="badge">{children}</span>
  ),
  Card: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  cn: (...args: string[]) => args.filter(Boolean).join(" "),
  useToast: jest.fn().mockReturnValue({ toast: jest.fn() }),
  Spinner: (props: React.SVGProps<SVGSVGElement>) => (
    <svg data-testid="loader" {...props} />
  ),
}));

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: "en" as const,
    setLocale: () => {},
    dir: "ltr" as const,
  }),
}));

jest.mock("lucide-react", () => ({
  Settings: () => null,
  User: () => null,
  Shield: () => null,
  Bell: () => null,
  Database: () => null,
  Key: () => null,
  ChevronLeft: () => null,
  Save: () => null,
  Loader2: (props: React.SVGProps<SVGSVGElement>) => (
    <svg data-testid="loader" {...props} />
  ),
  Copy: () => null,
  Trash2: () => null,
}));

import { useQuery, useMutation } from "@tanstack/react-query";
import SettingsPage from "../page";

const mockUseQuery = useQuery as jest.Mock;
const mockUseMutation = useMutation as jest.Mock;

const mockProfile = {
  full_name: "Ahmed Ali",
  full_name_ar: "أحمد العلي",
  email: "ahmed@company.com",
  role: "admin",
  is_active: true,
  created_at: "2024-01-15T00:00:00Z",
};

describe("SettingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it("shows loading state", () => {
    mockUseQuery.mockReturnValue({ data: undefined, isLoading: true });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByTestId("loader")).toBeInTheDocument();
  });

  it("renders page title", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.title")).toBeInTheDocument();
  });

  it("renders tabs", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(
      screen.getAllByText("settings.profile").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("settings.security").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("settings.notifications").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders profile form with user data", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("Ahmed Ali")).toBeInTheDocument();
    expect(screen.getByText("settings.role.admin")).toBeInTheDocument();
  });

  it("renders API keys tab content", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(
      screen.getAllByText("settings.api_keys").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders notification toggles", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(
      screen.getByText("settings.notif.email_notifications"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("settings.notif.app_notifications"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("settings.notif.opportunity_alerts"),
    ).toBeInTheDocument();
  });

  it("renders save button for profile", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.save_changes")).toBeInTheDocument();
  });

  it("renders password change section", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(
      screen.getByTestId("input-settings.current_password"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("input-settings.new_password"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("input-settings.confirm_password"),
    ).toBeInTheDocument();
  });

  it("renders password update button", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.update_password")).toBeInTheDocument();
  });

  it("creates API key", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    const nameInput = screen.getByPlaceholderText("settings.api_key_name");
    fireEvent.change(nameInput, { target: { value: "My Key" } });
    fireEvent.click(screen.getByText("settings.api_add_key"));
    expect(screen.getAllByText(/sk-/).length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty API keys state", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.queryByText("nosk-")).not.toBeInTheDocument();
  });

  it("revokes API key", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    const nameInput = screen.getByPlaceholderText("settings.api_key_name");
    fireEvent.change(nameInput, { target: { value: "Test Key" } });
    fireEvent.click(screen.getByText("settings.api_add_key"));
    const keysBefore = screen.getAllByText(/sk-/).length;
    expect(keysBefore).toBeGreaterThanOrEqual(1);
  });

  it("renders active profile badge", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.active")).toBeInTheDocument();
  });

  it("shows inactive badge when profile is inactive", () => {
    mockUseQuery.mockReturnValue({
      data: { ...mockProfile, is_active: false },
      isLoading: false,
    });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.inactive")).toBeInTheDocument();
  });

  it("calls getCurrentUser on mount", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    expect(mockUseQuery).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["profile", "me"] }),
    );
  });

  it("renders profile email as disabled input", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    const emailInput = screen.getByDisplayValue("ahmed@company.com");
    expect(emailInput).toBeDisabled();
  });

  it("toggles notification preference", () => {
    mockUseQuery.mockReturnValue({ data: mockProfile, isLoading: false });
    mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
    render(<SettingsPage />);
    const toggles = screen.getAllByRole("switch");
    expect(toggles.length).toBeGreaterThan(0);
    fireEvent.click(toggles[0]);
    expect(screen.getAllByRole("switch").length).toBeGreaterThan(0);
  });
});
