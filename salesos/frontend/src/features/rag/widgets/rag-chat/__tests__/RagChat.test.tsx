import { render, screen, fireEvent, waitFor } from "@testing-library/react"

beforeAll(() => {
  Element.prototype.scrollTo = jest.fn()
})

import { RagChatWidget } from "../RagChatWidget"

jest.mock("@/lib/ragQueries", () => ({
  useAskQuestion: jest.fn(),
}))

import { useAskQuestion } from "@/lib/ragQueries"

const mockUseAskQuestion = useAskQuestion as jest.MockedFunction<typeof useAskQuestion>

function setupMocks(overrides = {}) {
  const mockMutate = jest.fn()
  mockUseAskQuestion.mockReturnValue({
    mutateAsync: mockMutate,
    isPending: false,
    ...overrides,
  } as any)
  return { mockMutate }
}

const sampleAnswer = {
  answer: "هذه هي الإجابة من المساعد الذكي",
  citations: [
    { source: "document-1", text: "نص المصدر الأول", relevance: 0.95 },
    { source: "document-2", text: "نص المصدر الثاني", relevance: 0.80 },
  ],
}

describe("RagChatWidget", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("1. Empty State", () => {
    it("shows initial empty state", () => {
      setupMocks()
      render(<RagChatWidget />)
      expect(screen.getByText("اسأل سؤالاً للبدء")).toBeInTheDocument()
    })
  })

  describe("2. Send Message", () => {
    it("disables send button when input is empty", () => {
      setupMocks()
      render(<RagChatWidget />)
      expect(screen.getByText("إرسال")).toBeDisabled()
    })

    it("enables send button when input has text", () => {
      setupMocks()
      render(<RagChatWidget />)
      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      expect(screen.getByText("إرسال")).not.toBeDisabled()
    })

    it("sends message and shows user bubble", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockResolvedValue(sampleAnswer)
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "ما هو آخر تحديث؟" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("ما هو آخر تحديث؟")).toBeInTheDocument()
      })
    })

    it("shows AI response after sending", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockResolvedValue(sampleAnswer)
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("هذه هي الإجابة من المساعد الذكي")).toBeInTheDocument()
      })
    })

    it("shows loading state while waiting", () => {
      const { mockMutate } = setupMocks()
      mockUseAskQuestion.mockReturnValue({ mutateAsync: mockMutate, isPending: true } as any)
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      expect(screen.getByText("جاري البحث...")).toBeInTheDocument()
    })
  })

  describe("3. Citations", () => {
    it("shows citation count toggle", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockResolvedValue(sampleAnswer)
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("2 مصدر")).toBeInTheDocument()
      })
    })

    it("expands citations on click", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockResolvedValue(sampleAnswer)
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("2 مصدر")).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText("2 مصدر"))

      await waitFor(() => {
        expect(screen.getByText("document-1")).toBeInTheDocument()
        expect(screen.getByText("document-2")).toBeInTheDocument()
      })
    })
  })

  describe("4. Error State", () => {
    it("shows error message on failure", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockRejectedValue(new Error("Network error"))
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("عذراً، حدث خطأ في الحصول على الإجابة")).toBeInTheDocument()
      })
    })

    it("shows retry button on error", async () => {
      const { mockMutate } = setupMocks()
      mockMutate.mockRejectedValue(new Error("Network error"))
      render(<RagChatWidget />)

      const input = screen.getByPlaceholderText("اكتب سؤالك...")
      fireEvent.change(input, { target: { value: "سؤال" } })
      fireEvent.click(screen.getByText("إرسال"))

      await waitFor(() => {
        expect(screen.getByText("إعادة المحاولة")).toBeInTheDocument()
      })
    })
  })
})
