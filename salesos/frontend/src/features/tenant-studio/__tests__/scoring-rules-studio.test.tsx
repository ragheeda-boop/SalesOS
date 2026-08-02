import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ScoringRulesStudio } from "../ScoringRulesStudio";

const refetch = jest.fn();
const upsertMutate = jest.fn();
const evaluateMutate = jest.fn();

jest.mock("@/lib/hooks/scoringRulesQueries", () => ({
  useScoringRules: () => ({
    data: [
      {
        id: "rule-1",
        tenant_id: "t1",
        name: "Heavy intent",
        target_type: "company",
        dimension_weights: { buying_intent: 1 },
        boosts: [],
        active: true,
        schema_version: 1,
      },
    ],
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useUpsertScoringRule: () => ({
    mutate: upsertMutate,
    isPending: false,
  }),
  useEvaluateScoringRule: () => ({
    mutate: evaluateMutate,
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

describe("ScoringRulesStudio — FE-S10-04", () => {
  it("lists tip rules and shows fail-safe honesty", () => {
    render(<ScoringRulesStudio />);
    expect(screen.getByTestId("scoring-rules-honesty")).toHaveTextContent(
      /fail-safe/i,
    );
    expect(screen.getByTestId("scoring-rules-honesty")).toHaveTextContent(
      /in-memory/i,
    );
    expect(screen.getByTestId("scoring-rules-row")).toHaveTextContent(
      "Heavy intent",
    );
  });

  it("submits tip POST upsert payload", async () => {
    render(<ScoringRulesStudio />);
    fireEvent.change(screen.getByTestId("scoring-rules-name"), {
      target: { value: "My rule" },
    });
    fireEvent.click(screen.getByTestId("scoring-rules-submit"));
    await waitFor(() => {
      expect(upsertMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "My rule",
          target_type: "company",
          dimension_weights: expect.objectContaining({
            buying_intent: expect.any(Number),
          }),
        }),
        expect.any(Object),
      );
    });
  });

  it("submits tip POST evaluate payload", async () => {
    render(<ScoringRulesStudio />);
    fireEvent.click(screen.getByTestId("scoring-rules-evaluate"));
    await waitFor(() => {
      expect(evaluateMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          target_type: "company",
          dimension_scores: expect.objectContaining({
            buying_intent: 80,
          }),
        }),
        expect.any(Object),
      );
    });
  });
});
