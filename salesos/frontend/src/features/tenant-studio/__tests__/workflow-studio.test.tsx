import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { WorkflowStudio } from "../WorkflowStudio";

const refetch = jest.fn();
const upsertMutate = jest.fn();
const compileMutate = jest.fn();
const ephemeralMutate = jest.fn();

jest.mock("@/lib/hooks/workflowStudioQueries", () => ({
  useWorkflowCanvases: () => ({
    data: [
      {
        id: "c1",
        tenant_id: "t1",
        name: "Demo",
        description: "",
        trigger_type: "manual",
        nodes: [{ id: "n1", kind: "action", step_type: "log_message" }],
        schema_version: 1,
      },
    ],
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useUpsertWorkflowCanvas: () => ({
    mutate: upsertMutate,
    isPending: false,
  }),
  useCompileWorkflowCanvas: () => ({
    mutate: compileMutate,
    isPending: false,
    data: undefined,
  }),
  useCompileWorkflowCanvasEphemeral: () => ({
    mutate: ephemeralMutate,
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

describe("WorkflowStudio — FE-S10-03", () => {
  it("lists canvases and shows for_each-deferred honesty", () => {
    render(<WorkflowStudio />);
    expect(screen.getByTestId("workflow-studio-honesty")).toHaveTextContent(
      /for_each/i,
    );
    expect(screen.getByTestId("workflow-studio-honesty")).toHaveTextContent(
      /in-memory/i,
    );
    expect(screen.getByTestId("workflow-row")).toHaveTextContent("Demo");
  });

  it("submits tip POST canvas upsert", async () => {
    render(<WorkflowStudio />);
    fireEvent.change(screen.getByTestId("workflow-name"), {
      target: { value: "My flow" },
    });
    fireEvent.click(screen.getByTestId("workflow-submit"));
    await waitFor(() => {
      expect(upsertMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "My flow",
          nodes: expect.any(Array),
        }),
        expect.any(Object),
      );
    });
  });

  it("compiles a saved canvas", async () => {
    render(<WorkflowStudio />);
    fireEvent.click(screen.getByTestId("workflow-compile-c1"));
    await waitFor(() => {
      expect(compileMutate).toHaveBeenCalledWith("c1", expect.any(Object));
    });
  });
});
