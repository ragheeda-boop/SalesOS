import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AiModelTiersStudio } from "../AiModelTiersStudio";

const mockMutateAsync = jest.fn();
const mockToast = jest.fn();

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
  Input: ({ label, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }) => (
    <label>
      {label}
      <input {...props} />
    </label>
  ),
  Spinner: () => <span>Loading</span>,
  useToast: () => ({ toast: mockToast }),
}));

jest.mock("@/lib/hooks/aiModelTiersStudioQueries", () => ({
  useAiModelTierCatalog: () => ({
    data: { catalog: [], feature_ai_copilot: false, honesty: "catalog only" },
    isLoading: false,
    isError: false,
    refetch: jest.fn(),
  }),
  useAiModelTierDefaults: () => ({
    data: null,
    isLoading: false,
    isError: false,
    refetch: jest.fn().mockResolvedValue({ error: null }),
  }),
  useAiModelTiersResolve: () => ({
    data: null,
    isLoading: false,
    isError: false,
    refetch: jest.fn(),
  }),
}));

jest.mock("@/lib/hooks/adminQueries", () => {
  const plans = [
      {
        id: "plan-1",
        name: "Starter",
        tier: "starter",
        entitlements: {
          version: 1,
          domains: {},
          quotas: { seats: 5, ai_tokens_monthly: 100, connectors: 1, storage_mb: 100, api_calls_monthly: 1000 },
          deployment_tier: "pooled",
          support_sla: "standard",
          ai_model_tier: { default: "economy", allowed: ["economy"] },
        },
      },
  ];
  return {
    useAdminPlans: () => ({ data: plans, isLoading: false, isError: false }),
    useUpdateAdminPlan: () => ({ isPending: false, mutateAsync: mockMutateAsync }),
  };
});

describe("AiModelTiersStudio", () => {
  beforeEach(() => {
    mockMutateAsync.mockReset().mockResolvedValue({});
    mockToast.mockReset();
  });

  it("saves validated default and allowed tiers through the plan entitlement API", async () => {
    render(<AiModelTiersStudio />);

    await waitFor(() => expect(screen.getByTestId("ai-model-tiers-plan-select")).toHaveValue("plan-1"));
    fireEvent.change(screen.getByTestId("ai-model-tiers-default-select"), {
      target: { value: "standard" },
    });
    fireEvent.click(screen.getByTestId("ai-model-tiers-allowed-standard"));
    fireEvent.click(screen.getByTestId("ai-model-tiers-save-plan"));

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledTimes(1));
    expect(mockMutateAsync).toHaveBeenCalledWith({
      entitlements: expect.objectContaining({
        quotas: expect.objectContaining({ seats: 5 }),
        ai_model_tier: { default: "standard", allowed: ["economy", "standard"] },
      }),
    });
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: "Plan model tiers saved" }));
  });

  it("disables saving when the default tier is not allowed", async () => {
    render(<AiModelTiersStudio />);
    await waitFor(() => expect(screen.getByTestId("ai-model-tiers-plan-select")).toHaveValue("plan-1"));
    fireEvent.click(screen.getByTestId("ai-model-tiers-allowed-economy"));
    expect(screen.getByTestId("ai-model-tiers-save-plan")).toBeDisabled();
  });
});
