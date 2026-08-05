import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NotificationRulesStudio } from "../NotificationRulesStudio";

const refetch = jest.fn();
const upsertMutate = jest.fn();
const routeMutate = jest.fn();
const compileMutate = jest.fn();

jest.mock("@/lib/hooks/notificationRulesQueries", () => ({
  useNotificationEvents: () => ({
    data: {
      event_types: ["opportunity.stage_changed"],
      channels: ["in_app", "email"],
    },
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useNotificationRules: () => ({
    data: [
      {
        id: "nr1",
        tenant_id: "t1",
        name: "Won alert",
        event_type: "opportunity.stage_changed",
        channels: ["in_app"],
        recipients: [{ kind: "role", value: "sales" }],
        conditions: [],
        message_template: "won",
        priority: 100,
        active: true,
        schema_version: 1,
      },
    ],
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useUpsertNotificationRule: () => ({
    mutate: upsertMutate,
    isPending: false,
  }),
  useRouteNotificationEvent: () => ({
    mutate: routeMutate,
    isPending: false,
    data: undefined,
  }),
  useCompileNotificationRule: () => ({
    mutate: compileMutate,
    isPending: false,
    data: undefined,
  }),
}));

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: Record<string, unknown>) =>
    createElement("button", props, children),
  Input: ({ label, ...props }: Record<string, unknown>) =>
    createElement("label", null, label, createElement("input", props)),
  Spinner: () => createElement("div", { "data-testid": "spinner" }),
  useToast: () => ({ toast: jest.fn() }),
}));

describe("NotificationRulesStudio — FE-S10-08", () => {
  it("lists rules and shows RulesEngine honesty", () => {
    render(<NotificationRulesStudio />);
    expect(screen.getByTestId("notification-rules-honesty")).toHaveTextContent(/RulesEngine/i);
    expect(screen.getByTestId("notification-rules-honesty")).toHaveTextContent(/in-memory/i);
    expect(screen.getByTestId("notification-rules-row")).toHaveTextContent("Won alert");
  });

  it("submits tip POST upsert", async () => {
    render(<NotificationRulesStudio />);
    fireEvent.change(screen.getByTestId("notification-rules-name"), {
      target: { value: "Overdue" },
    });
    fireEvent.click(screen.getByTestId("notification-rules-submit"));
    await waitFor(() => {
      expect(upsertMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Overdue",
          channels: expect.any(Array),
          recipients: expect.any(Array),
        }),
        expect.any(Object)
      );
    });
  });
});
