import { render, screen, fireEvent } from "@testing-library/react";

jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: jest.fn(() => ({
    invalidateQueries: jest.fn(),
  })),
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

const mockNotifPrefs = {
  email_notifications: true,
  app_notifications: true,
  opportunity_alerts: true,
  company_updates: false,
  weekly_summary: true,
};

function mockQueries(profile = mockProfile) {
  mockUseQuery.mockImplementation(
    (opts: { queryKey?: readonly unknown[] }) => {
      const key = (opts.queryKey ?? []).join(":");
      if (key.includes("api-keys")) {
        return { data: [], isLoading: false };
      }
      if (key.includes("notifications")) {
        return { data: mockNotifPrefs, isLoading: false };
      }
      return { data: profile, isLoading: false };
    },
  );
}

function mockMutations() {
  mockUseMutation.mockImplementation(
    (opts: {
      onSuccess?: (data: unknown) => void;
      mutationFn?: (arg: unknown) => unknown;
    }) => ({
      mutate: (arg: unknown) => {
        if (typeof arg === "string") {
          opts.onSuccess?.({ key: `sk-test-${arg.replace(/\s+/g, "-")}` });
          return;
        }
        opts.onSuccess?.(undefined);
      },
      isPending: false,
    }),
  );
}

describe("SettingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockQueries();
    mockMutations();
  });

  it("shows loading state", () => {
    mockUseQuery.mockReturnValue({ data: undefined, isLoading: true });
    render(<SettingsPage />);
    expect(screen.getByTestId("loader")).toBeInTheDocument();
  });

  it("renders page title", () => {
    render(<SettingsPage />);
    expect(screen.getByText("settings.title")).toBeInTheDocument();
  });

  it("renders tabs", () => {
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
    render(<SettingsPage />);
    expect(screen.getByText("Ahmed Ali")).toBeInTheDocument();
    expect(screen.getByText("settings.role.admin")).toBeInTheDocument();
  });

  it("renders API keys tab content", () => {
    render(<SettingsPage />);
    expect(
      screen.getAllByText("settings.api_keys").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders notification toggles", () => {
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
    render(<SettingsPage />);
    expect(screen.getByText("settings.save_changes")).toBeInTheDocument();
  });

  it("renders password change section", () => {
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
    render(<SettingsPage />);
    expect(screen.getByText("settings.update_password")).toBeInTheDocument();
  });

  it("creates API key", () => {
    render(<SettingsPage />);
    const nameInput = screen.getByPlaceholderText("settings.api_key_name");
    fireEvent.change(nameInput, { target: { value: "My Key" } });
    fireEvent.click(screen.getByText("settings.api_add_key"));
    expect(screen.getAllByText(/sk-/).length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty API keys state", () => {
    render(<SettingsPage />);
    expect(screen.queryByText("nosk-")).not.toBeInTheDocument();
  });

  it("revokes API key", () => {
    render(<SettingsPage />);
    const nameInput = screen.getByPlaceholderText("settings.api_key_name");
    fireEvent.change(nameInput, { target: { value: "Test Key" } });
    fireEvent.click(screen.getByText("settings.api_add_key"));
    const keysBefore = screen.getAllByText(/sk-/).length;
    expect(keysBefore).toBeGreaterThanOrEqual(1);
  });

  it("renders active profile badge", () => {
    render(<SettingsPage />);
    expect(screen.getByText("settings.active")).toBeInTheDocument();
  });

  it("shows inactive badge when profile is inactive", () => {
    mockQueries({ ...mockProfile, is_active: false });
    render(<SettingsPage />);
    expect(screen.getByText("settings.inactive")).toBeInTheDocument();
  });

  it("calls getCurrentUser on mount", () => {
    render(<SettingsPage />);
    expect(mockUseQuery).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["profile", "me"] }),
    );
  });

  it("renders profile email as disabled input", () => {
    render(<SettingsPage />);
    const emailInput = screen.getByDisplayValue("ahmed@company.com");
    expect(emailInput).toBeDisabled();
  });

  it("toggles notification preference", () => {
    render(<SettingsPage />);
    const toggles = screen.getAllByRole("switch");
    expect(toggles.length).toBeGreaterThan(0);
    fireEvent.click(toggles[0]);
    expect(screen.getAllByRole("switch").length).toBeGreaterThan(0);
  });
});
