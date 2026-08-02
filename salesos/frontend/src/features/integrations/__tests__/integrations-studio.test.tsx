const replaceMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/integrations",
  useSearchParams: () => new URLSearchParams(),
}));

import { fireEvent, render, screen } from "@testing-library/react";
import { IntegrationsStudio } from "../IntegrationsStudio";

jest.mock("@/lib/hooks/integrationHubQueries", () => ({
  useHubConnection: () => ({
    data: undefined,
    isFetching: false,
    refetch: jest.fn(),
  }),
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

describe("IntegrationsStudio — FE-S08-08..14 / FE-S09-01..04", () => {
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

  it("exposes mapping version and schedule name (FE-S08-14)", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    expect(
      screen.getByTestId("integrations-studio-map-version"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("integrations-studio-step-schedule"));
    expect(
      screen.getByTestId("integrations-studio-schedule-name"),
    ).toBeInTheDocument();
  });

  it("exposes schedule job_type and conflict tip defaults (FE-S08-13)", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-schedule"));
    expect(
      screen.getByTestId("integrations-studio-schedule-job-type"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-connection-active-filter"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("integrations-studio-step-conflict"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-conflict-tip-defaults"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-connection-config"),
    ).toBeInTheDocument();
  });

  it("exposes monitor status/model filters (FE-S08-12)", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-monitor"));
    expect(
      screen.getByTestId("integrations-studio-monitor-status-filter"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-monitor-model-filter"),
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

  it("applies helpdesk.ticket preset and stage honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-helpdesk-ticket"),
    );
    expect(
      screen.getByTestId("integrations-studio-ticket-stage-honesty"),
    ).toHaveTextContent(/translated/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "helpdesk.ticket",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("stage_id");
  });

  it("applies project.task preset and TaskCaseExtension VO honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-project-task"),
    );
    expect(
      screen.getByTestId("integrations-studio-task-case-honesty"),
    ).toHaveTextContent(/Value Object|no independent id/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "project.task",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("stage_id");
  });

  it("applies account.move preset and CustomerInvoice payment honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-account-move"),
    );
    expect(
      screen.getByTestId("integrations-studio-invoice-payment-honesty"),
    ).toHaveTextContent(/PlatformBillingInvoice|out_invoice/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "account.move",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("payment_state");
  });

  it("applies mail.message note preset and PII honesty", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    fireEvent.click(
      screen.getByTestId("integrations-studio-model-preset-mail-message"),
    );
    expect(
      screen.getByTestId("integrations-studio-note-pii-honesty"),
    ).toHaveTextContent(/AI-GR-001/i);
    expect(screen.getByTestId("integrations-studio-map-model")).toHaveValue(
      "mail.message",
    );
    expect(
      (
        screen.getByTestId(
          "integrations-studio-map-json",
        ) as HTMLTextAreaElement
      ).value,
    ).toContain("body");
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
