import { fireEvent, render, screen } from "@testing-library/react";
import { IntegrationsStudio } from "../IntegrationsStudio";

jest.mock("@/lib/hooks/integrationHubQueries", () => ({
  useHubConnections: () => ({
    data: [
      {
        id: "c1",
        tenant_id: "t1",
        connector_key: "fake",
        name: "Demo",
        credential_ref: "vault:demo/fake",
        connection_config: {},
        cursor_state: {},
        is_active: true,
      },
    ],
    isLoading: false,
  }),
  useHubSyncRuns: () => ({ data: [], isLoading: false }),
  useHubConflictPolicy: () => ({
    data: {
      id: "p1",
      connection_id: "c1",
      rules: [],
      salesos_authored_fields: ["risk_score"],
      operational_fields: ["name"],
    },
    isLoading: false,
  }),
  useCreateHubConnection: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTestHubConnection: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateHubMapping: () => ({ mutateAsync: jest.fn(), isPending: false }),
  usePutHubConflictPolicy: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useScheduleHubSync: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDisconnectHubConnection: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
}));

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: { children: React.ReactNode }) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  Input: ({
    label,
    ...props
  }: {
    label?: string;
  } & React.InputHTMLAttributes<HTMLInputElement>) => (
    <label>
      {label}
      <input {...props} />
    </label>
  ),
  Spinner: () => <span>loading</span>,
  useToast: () => ({ toast: jest.fn() }),
}));

describe("IntegrationsStudio — FE-S08-08", () => {
  it("renders conflict-policy step and Odoo honesty", () => {
    render(<IntegrationsStudio />);
    expect(screen.getByTestId("integrations-studio")).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/conflict-policy/i);
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/OdooAdapter/i);
    expect(
      screen.getByTestId("integrations-studio-step-conflict"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("integrations-studio-step-conflict"));
    expect(
      screen.getByTestId("integrations-studio-conflict"),
    ).toBeInTheDocument();
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-conflict-submit"),
    ).toBeInTheDocument();
  });
});
