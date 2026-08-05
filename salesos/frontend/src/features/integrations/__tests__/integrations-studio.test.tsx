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
      {
        id: "c-odoo",
        tenant_id: "t1",
        connector_key: "odoo",
        name: "Odoo Demo",
        credential_ref: "vault:demo/odoo",
        connection_config: {},
        cursor_state: { "res.partner": "2026-08-01 12:00:00" },
        is_active: true,
      },
    ],
    isLoading: false,
  }),
  useHubSyncRuns: () => ({
    data: [
      {
        id: "run-cursor-1",
        connection_id: "c1",
        model: "res.partner",
        status: "success",
        records_pulled: 2,
        records_written: 1,
        records_failed: 1,
        started_at: "2026-08-02T10:00:00Z",
        finished_at: "2026-08-02T10:01:00Z",
        cursor_before: { "res.partner": "2026-08-01 00:00:00" },
        cursor_after: { "res.partner": "2026-08-02 10:00:00" },
      },
    ],
    isLoading: false,
    isFetching: false,
    refetch: jest.fn(),
  }),
  useHubUnlinkedBadges: () => ({
    data: {
      connection_id: "c1",
      count: 1,
      items: [
        {
          kind: "unlinked_badge",
          external_id: "ext-1",
          status: "unlinked",
          cr_number: "1010123456",
          message: "no golden match",
          sync_run_id: "run-1",
        },
      ],
    },
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
    ).toHaveTextContent(/credential/i);
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/HubSpot/i);
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
    ).toHaveTextContent(/registration|company|Monitor/i);
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
    ).toHaveTextContent(/stages|PII/i);
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
    ).toHaveTextContent(/case extensions|financing/i);
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
    ).toHaveTextContent(/Stripe|Customer invoices|AR/i);
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
    ).toHaveTextContent(/PII-scrubbed|audit-only/i);
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
  it("shows STORY-09-07 odoo flag + write_date cursor honesty when odoo selected", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-map"));
    const select = screen.getByTestId(
      "integrations-studio-connection-select",
    ) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "c-odoo" } });
    expect(
      screen.getByTestId("integrations-studio-odoo-flag-honesty"),
    ).toHaveTextContent(/feature_odoo_integration/i);
    expect(
      screen.getByTestId("integrations-studio-cursor-write-date-honesty"),
    ).toHaveTextContent(/write_date/i);
  });

  it("states operator limits in live honesty banner", () => {
    render(<IntegrationsStudio />);
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/credential|HubSpot|feature flag/i);
  });
  it("lists tip unlinked badges on Monitor (FE-S09-08)", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-monitor"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-unlinked-honesty"),
    ).toHaveTextContent(/Unlinked badges|residuals/i);
    expect(
      screen.getByTestId("integrations-studio-unlinked-count"),
    ).toHaveTextContent(/1 badge/);
    expect(
      screen.getByTestId("integrations-studio-unlinked-badge-row"),
    ).toHaveTextContent(/ext-1/);
  });
  it("shows tip SyncRun cursor_before/after on Monitor (FE-S09-09)", () => {
    render(<IntegrationsStudio />);
    fireEvent.click(screen.getByTestId("integrations-studio-step-monitor"));
    fireEvent.change(
      screen.getByTestId("integrations-studio-connection-select"),
      { target: { value: "c1" } },
    );
    expect(
      screen.getByTestId("integrations-studio-sync-run-cursors"),
    ).toHaveTextContent(/Cursors:/i);
    expect(
      screen.getByTestId("integrations-studio-sync-run-cursors"),
    ).toHaveTextContent(/before/);
  });
});
