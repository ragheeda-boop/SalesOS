import { render, screen } from "@testing-library/react";
import { useAccessToken } from "../../../_hooks/useAccessToken";
import { AiStudioWorkspace, type AiStudioSurface } from "../../_components/ai-studio-workspace";

jest.mock("../../../_hooks/useAccessToken", () => ({ useAccessToken: jest.fn() }));
jest.mock("@/features/tenant-studio/AiMemoryStudio", () => ({
  AiMemoryStudio: () => <div>Memory editor</div>,
}));
jest.mock("@/features/tenant-studio/AiModelTiersStudio", () => ({
  AiModelTiersStudio: () => <div>Model tier catalog</div>,
}));
jest.mock("@/features/tenant-studio/AiPoliciesStudio", () => ({
  AiPoliciesStudio: () => <div>Policy editor</div>,
}));
jest.mock("@/features/tenant-studio/PromptLibraryStudio", () => ({
  PromptLibraryStudio: () => <div>Prompt editor</div>,
}));

const accessTokenMock = useAccessToken as jest.MockedFunction<typeof useAccessToken>;

const cases: { surface: AiStudioSurface; title: string; content: string }[] = [
  { surface: "prompts", title: "Prompt Library", content: "Prompt editor" },
  { surface: "policies", title: "AI Policies", content: "Policy editor" },
  { surface: "memory", title: "AI Memory", content: "Memory editor" },
  { surface: "model-tiers", title: "AI Model Tiers", content: "Model tier catalog" },
];

describe("AiStudioWorkspace", () => {
  beforeEach(() => {
    accessTokenMock.mockReturnValue({ ready: true, hasToken: true, audienceKind: "tenant" });
  });

  it.each(cases)("renders the $title workspace with its honest status", ({ surface, title, content }) => {
    render(<AiStudioWorkspace surface={surface} />);

    expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    expect(screen.getByText(content)).toBeInTheDocument();
    expect(screen.getByRole("note")).toBeInTheDocument();
  });

  it("does not render admin tools before authentication", () => {
    accessTokenMock.mockReturnValue({ ready: true, hasToken: false, audienceKind: null });

    render(<AiStudioWorkspace surface="prompts" />);

    expect(screen.getByText("Sign in required")).toBeInTheDocument();
    expect(screen.queryByText("Prompt editor")).not.toBeInTheDocument();
  });
});
