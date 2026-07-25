import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import NewWorkflowPage from "../page"

const mockMutateAsync = jest.fn()
const mockToast = jest.fn()

jest.mock("@/lib/workflowQueries", () => ({
  useCreateWorkflow: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
  useUpdateWorkflow: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
}))

jest.mock("@/lib/i18n", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}))

jest.mock("@salesos/ui", () => ({
  cn: (...args: (string | undefined | false)[]) => args.filter(Boolean).join(" "),
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
  Button: ({ children, onClick, disabled, leftIcon, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {leftIcon}
      {children}
    </button>
  ),
  Input: (props: any) => <input {...props} />,
  Textarea: (props: any) => <textarea {...props} />,
  Select: ({ options, value, onChange }: any) => (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {options?.map((o: any) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  ),
  useToast: () => ({ toast: mockToast }),
}))

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}))

jest.mock("next/link", () => {
  function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>
  }
  MockLink.displayName = "MockLink"
  return MockLink
})

describe("NewWorkflowPage", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("1. Page renders", () => {
    it("renders the page title", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("مُنشئ سير العمل")).toBeInTheDocument()
    })

    it("renders the back link to automation", () => {
      render(<NewWorkflowPage />)
      const links = screen.getAllByRole("link")
      const backLink = links.find((l) => l.getAttribute("href") === "/automation")
      expect(backLink).toBeTruthy()
    })

    it("renders save and test buttons", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("حفظ")).toBeInTheDocument()
      expect(screen.getByText("اختبار")).toBeInTheDocument()
    })
  })

  describe("2. Workflow settings sidebar", () => {
    it("renders workflow name input", () => {
      render(<NewWorkflowPage />)
      const nameInput = screen.getByPlaceholderText("اسم سير العمل")
      expect(nameInput).toBeInTheDocument()
    })

    it("renders trigger type selector", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("نوع المشغل")).toBeInTheDocument()
    })

    it("renders status selector", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("الحالة")).toBeInTheDocument()
    })
  })

  describe("3. Step palette", () => {
    it("renders all step type buttons", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("إرسال بريد")).toBeInTheDocument()
      expect(screen.getByText("تحديث سجل")).toBeInTheDocument()
      expect(screen.getByText("إنشاء مهمة")).toBeInTheDocument()
      expect(screen.getByText("Webhook")).toBeInTheDocument()
      expect(screen.getByText("توصية ذكية")).toBeInTheDocument()
    })

    it("adds a step when clicking a step type", () => {
      render(<NewWorkflowPage />)
      const addButtons = screen.getAllByText("إرسال بريد")
      // Click the palette button (second one, first is in sidebar)
      fireEvent.click(addButtons[1])
      expect(screen.getByText("الخطوات (1)")).toBeInTheDocument()
    })
  })

  describe("4. Empty canvas state", () => {
    it("shows empty state message", () => {
      render(<NewWorkflowPage />)
      expect(screen.getByText("أضف خطوة للبدء")).toBeInTheDocument()
    })
  })

  describe("5. Validation", () => {
    it("shows error toast when saving without name", () => {
      render(<NewWorkflowPage />)
      fireEvent.click(screen.getByText("حفظ"))
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error" })
      )
    })
  })

  describe("6. Test run", () => {
    it("shows error when testing empty workflow", () => {
      render(<NewWorkflowPage />)
      fireEvent.click(screen.getByText("اختبار"))
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "error" })
      )
    })
  })
})
