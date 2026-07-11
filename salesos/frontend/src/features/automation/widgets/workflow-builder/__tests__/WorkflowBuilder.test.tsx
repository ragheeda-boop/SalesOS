import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { WorkflowBuilderWidget } from "../WorkflowBuilderWidget"

jest.mock("@/lib/workflowQueries", () => ({
  useWorkflows: jest.fn(),
  useCreateWorkflow: jest.fn(),
  useUpdateWorkflow: jest.fn(),
  useDeleteWorkflow: jest.fn(),
  useExecuteWorkflow: jest.fn(),
  useWorkflowExecutions: jest.fn(),
}))

import { useWorkflows, useCreateWorkflow, useExecuteWorkflow, useDeleteWorkflow } from "@/lib/workflowQueries"

const mockUseWorkflows = useWorkflows as jest.MockedFunction<typeof useWorkflows>
const mockUseCreateWorkflow = useCreateWorkflow as jest.MockedFunction<typeof useCreateWorkflow>
const mockUseExecuteWorkflow = useExecuteWorkflow as jest.MockedFunction<typeof useExecuteWorkflow>
const mockUseDeleteWorkflow = useDeleteWorkflow as jest.MockedFunction<typeof useDeleteWorkflow>

const sampleWorkflows = [
  { id: "wf-1", name: "متابعة العميل", description: "سير عمل متابعة", trigger_type: "event", trigger_config: {}, steps: [{ id: "s1", type: "send_email", config: {}, order: 0 }], status: "active", created_at: "2026-07-10T10:00:00Z", updated_at: "2026-07-10T10:00:00Z" },
  { id: "wf-2", name: "مراجعة الصفقة", description: "", trigger_type: "manual", trigger_config: {}, steps: [], status: "draft", created_at: "2026-07-11T10:00:00Z", updated_at: "2026-07-11T10:00:00Z" },
]

function setupMocks(overrides = {}) {
  const mockCreateMutate = jest.fn()
  const mockExecuteMutate = jest.fn()
  const mockDeleteMutate = jest.fn()

  mockUseWorkflows.mockReturnValue({ data: sampleWorkflows, isLoading: false, error: null, ...overrides } as any)
  mockUseCreateWorkflow.mockReturnValue({ mutateAsync: mockCreateMutate, isPending: false } as any)
  mockUseExecuteWorkflow.mockReturnValue({ mutateAsync: mockExecuteMutate, isPending: false } as any)
  mockUseDeleteWorkflow.mockReturnValue({ mutateAsync: mockDeleteMutate, isPending: false } as any)

  return { mockCreateMutate, mockExecuteMutate, mockDeleteMutate }
}

describe("WorkflowBuilderWidget", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    window.confirm = jest.fn(() => true)
  })

  describe("1. Loading State", () => {
    it("renders loading skeleton", () => {
      mockUseWorkflows.mockReturnValue({ data: null, isLoading: true, error: null } as any)
      render(<WorkflowBuilderWidget />)
      const skeletons = document.querySelectorAll(".animate-pulse")
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe("2. Error State", () => {
    it("renders error message", () => {
      mockUseWorkflows.mockReturnValue({ data: null, isLoading: false, error: new Error("fail") } as any)
      render(<WorkflowBuilderWidget />)
      expect(screen.getByText("فشل تحميل سير العمل")).toBeInTheDocument()
    })
  })

  describe("3. Empty State", () => {
    it("renders empty state when no workflows", () => {
      mockUseWorkflows.mockReturnValue({ data: [], isLoading: false, error: null } as any)
      render(<WorkflowBuilderWidget />)
      expect(screen.getByText("لا توجد سير عمل بعد")).toBeInTheDocument()
    })
  })

  describe("4. Loaded State", () => {
    it("renders workflow list", () => {
      setupMocks()
      render(<WorkflowBuilderWidget />)
      expect(screen.getByText("متابعة العميل")).toBeInTheDocument()
      expect(screen.getByText("مراجعة الصفقة")).toBeInTheDocument()
    })

    it("shows status badges", () => {
      setupMocks()
      render(<WorkflowBuilderWidget />)
      expect(screen.getByText("نشط")).toBeInTheDocument()
      expect(screen.getByText("مسودة")).toBeInTheDocument()
    })

    it("shows trigger type", () => {
      setupMocks()
      render(<WorkflowBuilderWidget />)
      expect(screen.getByText("حدث")).toBeInTheDocument()
      expect(screen.getByText("يدوي")).toBeInTheDocument()
    })
  })

  describe("5. Create Workflow", () => {
    it("opens form on create button click", () => {
      setupMocks()
      render(<WorkflowBuilderWidget />)
      fireEvent.click(screen.getByText("إنشاء سير عمل"))
      expect(screen.getByText("إنشاء سير عمل")).toBeInTheDocument()
    })

    it("creates workflow on save", async () => {
      const { mockCreateMutate } = setupMocks()
      render(<WorkflowBuilderWidget />)
      fireEvent.click(screen.getByText("إنشاء سير عمل"))
      const nameInput = screen.getByLabelText("الاسم") as HTMLInputElement
      fireEvent.change(nameInput, { target: { value: "سير عمل جديد" } })
      fireEvent.click(screen.getByText("حفظ"))
      await waitFor(() => {
        expect(mockCreateMutate).toHaveBeenCalled()
      })
    })
  })

  describe("6. Execute Workflow", () => {
    it("shows confirmation before execute", () => {
      const { mockExecuteMutate } = setupMocks()
      render(<WorkflowBuilderWidget />)
      const executeButtons = screen.getAllByText("تنفيذ")
      fireEvent.click(executeButtons[0])
      expect(screen.getByText("تأكيد التنفيذ؟")).toBeInTheDocument()
    })

    it("executes after confirmation", async () => {
      const { mockExecuteMutate } = setupMocks()
      render(<WorkflowBuilderWidget />)
      const executeButtons = screen.getAllByText("تنفيذ")
      fireEvent.click(executeButtons[0])
      fireEvent.click(screen.getByText("نعم"))
      await waitFor(() => {
        expect(mockExecuteMutate).toHaveBeenCalledWith("wf-1")
      })
    })
  })

  describe("7. Delete Workflow", () => {
    it("calls delete with confirmation", async () => {
      const { mockDeleteMutate } = setupMocks()
      render(<WorkflowBuilderWidget />)
      const deleteButtons = screen.getAllByText("حذف")
      fireEvent.click(deleteButtons[0])
      await waitFor(() => {
        expect(mockDeleteMutate).toHaveBeenCalledWith("wf-1")
      })
    })
  })
})
