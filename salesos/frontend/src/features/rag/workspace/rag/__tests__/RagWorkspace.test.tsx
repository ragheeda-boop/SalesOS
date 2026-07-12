import { render, screen } from "@testing-library/react"

jest.mock("../../../widgets/rag-chat/RagChatWidget", () => ({
  RagChatWidget: () => <div data-testid="rag-chat-widget">RagChatWidget</div>,
}))

jest.mock("../../../widgets/rag-documents/RagDocumentManager", () => ({
  RagDocumentManager: () => <div data-testid="rag-document-manager">RagDocumentManager</div>,
}))

import { RagWorkspace } from "../RagWorkspace"

describe("RagWorkspace", () => {
  it("renders layout composition with chat and documents", () => {
    render(<RagWorkspace />)

    expect(screen.getByTestId("rag-chat-widget")).toBeInTheDocument()
    expect(screen.getByTestId("rag-document-manager")).toBeInTheDocument()
  })

  it("renders heading", () => {
    render(<RagWorkspace />)

    expect(screen.getByText("المساعد الذكي")).toBeInTheDocument()
  })

  it("contains both sections in a grid", () => {
    const { container } = render(<RagWorkspace />)

    const grid = container.querySelector(".grid")
    expect(grid).toBeInTheDocument()
    expect(grid).toContainElement(screen.getByTestId("rag-chat-widget"))
    expect(grid).toContainElement(screen.getByTestId("rag-document-manager"))
  })
})
