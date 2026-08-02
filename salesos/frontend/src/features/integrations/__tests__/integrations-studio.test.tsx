const replaceMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/integrations",
  useSearchParams: () => new URLSearchParams(),
}));

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
  useHubSyncRuns: () => ({
    data: [],
    isLoading: false,
    isFetching: false,
    refetch: jest.fn(),
  }),
  useActiveHubMapping: () => ({
    data: {
      id: "m1",
      connection_id: "c1",
      model: "company",
      version: 2,
      mappings: [{ external: "name", internal: "name" }],
      baseline_fields: [],
      is_active: true,
    },
    isLoading: false,
    isFetching: false,
    refetch: jest.fn(),
  }),
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

describe("IntegrationsStudio — FE-S08-08..11 / FE-S09-01/02", () => {
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

  it("loads active mapping on Map step", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-map-load"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-map-active-status"),
    ).toHaveTextContent(/Active v2/i);
  });

  it("shows connection detail and map baseline fields", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-connection-detail"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-connection-key"),
    ).toHaveTextContent(/fake/);
    expect(
      screen.getByTestId("integrations-studio-map-baseline"),
    ).toBeInTheDocument();
  });

  it("requires disconnect confirmation", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-disconnect"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-disconnect-submit"),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByTestId("integrations-studio-disconnect-confirm"),
    );
    expect(
      screen.getByTestId("integrations-studio-disconnect-submit"),
    ).not.toBeDisabled();
  });

  it("exposes monitor status filter and schedule result hook", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-monitor"));
    expect(
      screen.getByTestId("integrations-studio-monitor-status-filter"),
    ).toBeInTheDocument();
  });

  it("applies res.partner preset and cr_number join honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-res-partner"),
    );
    expect(
      screen.getByTestId("integrations-studio-partner-join-honesty"),
    ).toHaveTextContent(/cr_number/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "res.partner",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("x_studio_cr_number");
  });

  it("applies crm.lead opportunity preset and stage honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-crm-lead"),
    );
    expect(
      screen.getByTestId("integrations-studio-opportunity-stage-honesty"),
    ).toHaveTextContent(/translated/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "crm.lead",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("stage_id");
  });
});
