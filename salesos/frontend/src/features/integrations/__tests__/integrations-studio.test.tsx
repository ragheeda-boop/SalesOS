import { render, screen } from "@testing-library/react";
import { IntegrationsStudio } from "../IntegrationsStudio";

jest.mock("@/lib/hooks/integrationHubQueries", () => ({
  useHubConnections: () => ({ data: [], isLoading: false }),
  useHubSyncRuns: () => ({ data: [], isLoading: false }),
  useCreateHubConnection: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTestHubConnection: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateHubMapping: () => ({ mutateAsync: jest.fn(), isPending: false }),
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

describe("IntegrationsStudio — STORY-08-07", () => {
  it("renders live Hub honesty and enabled connect panel", () => {
    render(<IntegrationsStudio />);
    expect(screen.getByTestId("integrations-studio")).toBeInTheDocument();
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/STORY-08-06/);
    expect(
      screen.getByTestId("integrations-studio-live-honesty"),
    ).toHaveTextContent(/Not Production GO/);
    expect(
      screen.getByTestId("integrations-studio-step-connect"),
    ).not.toBeDisabled();
    expect(
      screen.getByTestId("integrations-studio-connect-submit"),
    ).toBeInTheDocument();
  });
});
