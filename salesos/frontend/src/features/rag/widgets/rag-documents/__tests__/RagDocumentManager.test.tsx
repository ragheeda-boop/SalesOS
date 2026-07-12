import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { RagDocumentManager } from "../RagDocumentManager"

jest.mock("@/lib/ragQueries", () => ({
  useRagDocuments: jest.fn(),
  useIngestDocument: jest.fn(),
  useDeleteDocument: jest.fn(),
}))

import { useRagDocuments, useIngestDocument, useDeleteDocument } from "@/lib/ragQueries"

const mockUseRagDocuments = useRagDocuments as jest.MockedFunction<typeof useRagDocuments>
const mockUseIngestDocument = useIngestDocument as jest.MockedFunction<typeof useIngestDocument>
const mockUseDeleteDocument = useDeleteDocument as jest.MockedFunction<typeof useDeleteDocument>

const sampleDocs = [
  { id: "d1", title: "مستند أول", content: "محتوى المستند الأول", source_type: "email" as const, created_at: "2026-01-15T10:00:00Z" },
  { id: "d2", title: "اجتماع", content: "محضر اجتماع", source_type: "meeting" as const, created_at: "2026-02-20T14:00:00Z" },
  { id: "d3", title: "ملاحظة", content: "ملاحظات عامة", source_type: "note" as const, created_at: "2026-03-10T09:00:00Z" },
]

function setupMocks(docOverrides = {}, ingestOverrides = {}, deleteOverrides = {}) {
  const mockIngestMutate = jest.fn().mockResolvedValue({})
  const mockDeleteMutate = jest.fn().mockResolvedValue(undefined)

  mockUseRagDocuments.mockReturnValue({
    data: sampleDocs,
    isLoading: false,
    error: null,
    ...docOverrides,
  } as any)

  mockUseIngestDocument.mockReturnValue({
    mutateAsync: mockIngestMutate,
    isPending: false,
    ...ingestOverrides,
  } as any)

  mockUseDeleteDocument.mockReturnValue({
    mutateAsync: mockDeleteMutate,
    isPending: false,
    ...deleteOverrides,
  } as any)

  return { mockIngestMutate, mockDeleteMutate }
}

describe("RagDocumentManager", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("1. Document List", () => {
    it("renders document titles", () => {
      setupMocks()
      render(<RagDocumentManager />)

      expect(screen.getByText("مستند أول")).toBeInTheDocument()
      expect(screen.getAllByText("اجتماع").length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText("ملاحظة").length).toBeGreaterThanOrEqual(1)
    })

    it("renders document content previews", () => {
      setupMocks()
      render(<RagDocumentManager />)

      expect(screen.getByText("محتوى المستند الأول")).toBeInTheDocument()
      expect(screen.getByText("محضر اجتماع")).toBeInTheDocument()
      expect(screen.getByText("ملاحظات عامة")).toBeInTheDocument()
    })

    it("renders source type labels", () => {
      setupMocks()
      render(<RagDocumentManager />)

      expect(screen.getAllByText("بريد").length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText("اجتماع").length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText("ملاحظة").length).toBeGreaterThanOrEqual(1)
    })

    it("renders header with title", () => {
      setupMocks()
      render(<RagDocumentManager />)

      expect(screen.getByText("المستندات")).toBeInTheDocument()
    })
  })

  describe("2. Ingest Modal", () => {
    it("does not show modal initially", () => {
      setupMocks()
      render(<RagDocumentManager />)

      expect(screen.queryByText("إضافة مستند")).not.toBeInTheDocument()
    })

    it("opens modal on add button click", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))

      expect(screen.getByText("إضافة مستند")).toBeInTheDocument()
      expect(screen.getByText("العنوان")).toBeInTheDocument()
      expect(screen.getByText("المحتوى")).toBeInTheDocument()
    })

    it("closes modal on cancel", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))
      fireEvent.click(screen.getByText("إلغاء"))

      expect(screen.queryByText("إضافة مستند")).not.toBeInTheDocument()
    })

    it("closes modal on close button", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))
      fireEvent.click(screen.getByText("✕"))

      expect(screen.queryByText("إضافة مستند")).not.toBeInTheDocument()
    })
  })

  describe("3. Form Submission", () => {
    it("disables submit when title is empty", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))

      const submitBtn = screen.getByRole("button", { name: "إضافة" })
      expect(submitBtn).toBeDisabled()
    })

    it("enables submit when form is filled", async () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))

      const titleInput = document.querySelector('input') as HTMLInputElement
      fireEvent.change(titleInput, { target: { value: "عنوان جديد" } })
      const textarea = document.querySelector("textarea") as HTMLTextAreaElement
      fireEvent.change(textarea, { target: { value: "محتوى جديد" } })

      const submitBtn = screen.getByRole("button", { name: "إضافة" })
      expect(submitBtn).not.toBeDisabled()
    })

    it("submits and resets form", async () => {
      const { mockIngestMutate } = setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))

      const titleInput = document.querySelector('input') as HTMLInputElement
      fireEvent.change(titleInput, { target: { value: "عنوان جديد" } })
      const textarea = document.querySelector("textarea") as HTMLTextAreaElement
      fireEvent.change(textarea, { target: { value: "محتوى جديد" } })

      fireEvent.click(screen.getByRole("button", { name: "إضافة" }))

      await waitFor(() => {
        expect(mockIngestMutate).toHaveBeenCalledWith({
          title: "عنوان جديد",
          content: "محتوى جديد",
          source_type: "note",
        })
      })
    })

    it("closes modal after successful submission", async () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("+ إضافة"))

      const titleInput = document.querySelector('input') as HTMLInputElement
      fireEvent.change(titleInput, { target: { value: "عنوان" } })
      const textarea = document.querySelector("textarea") as HTMLTextAreaElement
      fireEvent.change(textarea, { target: { value: "محتوى" } })

      fireEvent.click(screen.getByRole("button", { name: "إضافة" }))

      await waitFor(() => {
        expect(screen.queryByText("إضافة مستند")).not.toBeInTheDocument()
      })
    })
  })

  describe("4. Delete Confirmation", () => {
    it("shows delete button for each document", () => {
      setupMocks()
      render(<RagDocumentManager />)

      const deleteButtons = screen.getAllByText("حذف")
      expect(deleteButtons.length).toBe(3)
    })

    it("shows confirmation on delete click", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getAllByText("حذف")[0])

      expect(screen.getByText("تأكيد")).toBeInTheDocument()
      expect(screen.getByText("إلغاء")).toBeInTheDocument()
    })

    it("cancels delete confirmation", () => {
      setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getAllByText("حذف")[0])
      fireEvent.click(screen.getByText("إلغاء"))

      expect(screen.queryByText("تأكيد")).not.toBeInTheDocument()
    })

    it("executes delete on confirm", async () => {
      const { mockDeleteMutate } = setupMocks()
      render(<RagDocumentManager />)

      fireEvent.click(screen.getAllByText("حذف")[0])
      fireEvent.click(screen.getByText("تأكيد"))

      await waitFor(() => {
        expect(mockDeleteMutate).toHaveBeenCalledWith("d1")
      })
    })
  })

  describe("5. Empty State", () => {
    it("shows empty state when no documents", () => {
      setupMocks({ data: [] })
      render(<RagDocumentManager />)

      expect(screen.getByText("لا توجد مستندات")).toBeInTheDocument()
      expect(screen.getByText("إضافة مستند جديد")).toBeInTheDocument()
    })

    it("empty state add button opens modal", () => {
      setupMocks({ data: [] })
      render(<RagDocumentManager />)

      fireEvent.click(screen.getByText("إضافة مستند جديد"))

      expect(screen.getByText("إضافة مستند")).toBeInTheDocument()
    })
  })

  describe("6. Loading State", () => {
    it("shows skeleton placeholders while loading", () => {
      setupMocks({ isLoading: true, data: undefined })
      render(<RagDocumentManager />)

      expect(screen.queryByText("حذف")).not.toBeInTheDocument()
    })
  })

  describe("7. Error State", () => {
    it("shows error message on fetch failure", () => {
      setupMocks({ error: new Error("Network error"), data: undefined })
      render(<RagDocumentManager />)

      expect(screen.getByText("فشل تحميل المستندات")).toBeInTheDocument()
    })
  })
})
