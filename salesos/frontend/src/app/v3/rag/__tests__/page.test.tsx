import { render, screen } from "@testing-library/react";
import { useAccessToken } from "../../_hooks/useAccessToken";
import V3RagPage from "../page";

jest.mock("../../_hooks/useAccessToken", () => ({
  useAccessToken: jest.fn(),
}));
jest.mock("@/features/rag/workspace/rag/RagWorkspace", () => ({
  RagWorkspace: () => <div>RAG chat and document manager</div>,
}));

const accessTokenMock = useAccessToken as jest.MockedFunction<typeof useAccessToken>;

describe("V3RagPage", () => {
  it("shows the tenant knowledge workspace for an authenticated session", () => {
    accessTokenMock.mockReturnValue({ ready: true, hasToken: true, audienceKind: "tenant" });

    render(<V3RagPage />);

    expect(screen.getByRole("heading", { name: "Knowledge workspace" })).toBeInTheDocument();
    expect(screen.getByText("RAG chat and document manager")).toBeInTheDocument();
  });

  it("requires sign in before rendering tenant documents", () => {
    accessTokenMock.mockReturnValue({ ready: true, hasToken: false, audienceKind: null });

    render(<V3RagPage />);

    expect(screen.getByText("Sign in required")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/login?next=%2Fv3%2Frag"
    );
    expect(screen.queryByText("RAG chat and document manager")).not.toBeInTheDocument();
  });
});
