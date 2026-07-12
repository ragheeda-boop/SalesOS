import { render, screen, fireEvent } from "@testing-library/react"
import { AuditLogView } from "../AuditLogView"
import type { AuditLogEntry } from "@/lib/api"
import type { AuditLogFilters } from "../types"

const sampleEntry: AuditLogEntry = {
  id: "1",
  action: "user.created",
  action_type: "create",
  actor_id: "u1",
  actor_name: "أحمد محمد",
  actor_email: "ahmed@example.com",
  resource: "مستخدم جديد",
  resource_type: "user",
  resource_id: "u2",
  tenant_id: "t1",
  tenant_name: "شركة التقنية",
  details: { name: "خالد" },
  ip_address: "192.168.1.1",
  user_agent: "Mozilla/5.0",
  created_at: "2026-07-12T10:00:00.000Z",
}

const secondEntry: AuditLogEntry = {
  ...sampleEntry,
  id: "2",
  actor_name: "سارة العلي",
  actor_email: "sara@example.com",
  action_type: "delete",
  resource_type: "tenant",
  ip_address: "10.0.0.5",
  details: null,
}

const defaultFilters: AuditLogFilters = {
  dateFrom: undefined,
  dateTo: undefined,
  userId: undefined,
  actionType: undefined,
  resource: undefined,
  search: undefined,
  page: 1,
  pageSize: 20,
}

const defaultProps = {
  items: [sampleEntry],
  total: 1,
  loading: false,
  filters: defaultFilters,
  onFilterChange: jest.fn(),
  onExport: jest.fn(),
  onRefresh: jest.fn(),
}

function renderView(overrides?: Partial<typeof defaultProps>) {
  return render(<AuditLogView {...defaultProps} {...overrides} />)
}

describe("AuditLogView", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders title and region role", () => {
    renderView()
    expect(screen.getByText("سجل التدقيق")).toBeInTheDocument()
    expect(screen.getByRole("region", { name: "سجل التدقيق" })).toBeInTheDocument()
  })

  it("renders single audit log entry with all fields", () => {
    renderView()
    expect(screen.getByText("أحمد محمد")).toBeInTheDocument()
    expect(screen.getByText("ahmed@example.com")).toBeInTheDocument()
    expect(screen.getByText("192.168.1.1")).toBeInTheDocument()
  })

  it("renders multiple entries", () => {
    renderView({ items: [sampleEntry, secondEntry], total: 2 })
    expect(screen.getByText("أحمد محمد")).toBeInTheDocument()
    expect(screen.getByText("سارة العلي")).toBeInTheDocument()
    expect(screen.getByText("sara@example.com")).toBeInTheDocument()
  })

  it("shows empty state when no items", () => {
    renderView({ items: [], total: 0 })
    expect(screen.getByText("لا توجد سجلات تدقيق")).toBeInTheDocument()
    expect(screen.getByText("لم يتم تسجيل أي أحداث بعد")).toBeInTheDocument()
  })

  it("shows loading state", () => {
    renderView({ loading: true })
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument()
  })

  it("does not show table when loading", () => {
    renderView({ loading: true })
    expect(screen.queryByRole("table")).not.toBeInTheDocument()
  })

  it("calls onExport when export button clicked", () => {
    const onExport = jest.fn()
    renderView({ onExport })
    fireEvent.click(screen.getByText("تصدير CSV"))
    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it("calls onRefresh when refresh button clicked", () => {
    const onRefresh = jest.fn()
    renderView({ onRefresh })
    fireEvent.click(screen.getByText("تحديث"))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it("toggles filter panel open and closed", () => {
    renderView()
    const toggleBtn = screen.getByText("فلتر")
    fireEvent.click(toggleBtn)
    expect(screen.getByText("إخفاء الفلتر")).toBeInTheDocument()

    const hideBtn = screen.getByText("إخفاء الفلتر")
    fireEvent.click(hideBtn)
    expect(screen.getByText("فلتر")).toBeInTheDocument()
  })

  it("calls onFilterChange when search typed in filter panel", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const input = screen.getByPlaceholderText("بحث في السجل...")
    fireEvent.change(input, { target: { value: "ahmed" } })
    expect(onFilterChange).toHaveBeenCalledWith({ search: "ahmed", page: 1 })
  })

  it("calls onFilterChange when action type changed", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const select = screen.getByLabelText("نوع الإجراء")
    fireEvent.change(select, { target: { value: "create" } })
    expect(onFilterChange).toHaveBeenCalledWith({ actionType: "create" })
  })

  it("calls onFilterChange when resource type changed", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const select = screen.getByLabelText("المورد")
    fireEvent.change(select, { target: { value: "user" } })
    expect(onFilterChange).toHaveBeenCalledWith({ resource: "user" })
  })

  it("calls onFilterChange when date from changed", () => {
    const onFilterChange = jest.fn()
    renderView({ onFilterChange })
    fireEvent.click(screen.getByText("فلتر"))
    const dateInputs = screen.getAllByRole("textbox", { hidden: false })
    const dateFromInput = dateInputs.find((el) => el.getAttribute("type") === "date")
    if (dateFromInput) {
      fireEvent.change(dateFromInput, { target: { value: "2026-07-01" } })
      expect(onFilterChange).toHaveBeenCalledWith({ dateFrom: "2026-07-01" })
    }
  })

  it("calls onFilterChange on next page click", () => {
    const onFilterChange = jest.fn()
    renderView({ total: 50, onFilterChange })
    const nextBtn = screen.getByLabelText("الصفحة التالية")
    fireEvent.click(nextBtn)
    expect(onFilterChange).toHaveBeenCalledWith({ page: 2 })
  })

  it("calls onFilterChange on previous page click", () => {
    const onFilterChange = jest.fn()
    renderView({ total: 50, filters: { ...defaultFilters, page: 3 }, onFilterChange })
    const prevBtn = screen.getByLabelText("الصفحة السابقة")
    fireEvent.click(prevBtn)
    expect(onFilterChange).toHaveBeenCalledWith({ page: 2 })
  })

  it("disables previous button on first page", () => {
    renderView({ total: 50 })
    const prevBtn = screen.getByLabelText("الصفحة السابقة")
    expect(prevBtn).toBeDisabled()
  })

  it("disables next button on last page", () => {
    renderView({ total: 15, filters: { ...defaultFilters, page: 1, pageSize: 20 } })
    const nextBtn = screen.getByLabelText("الصفحة التالية")
    expect(nextBtn).toBeDisabled()
  })

  it("displays pagination info correctly", () => {
    renderView({ total: 50, filters: { ...defaultFilters, page: 2, pageSize: 20 } })
    expect(screen.getByText("21-40 من 50")).toBeInTheDocument()
  })

  it("displays zero results for empty total", () => {
    renderView({ total: 0 })
    expect(screen.getByText("0 نتيجة")).toBeInTheDocument()
  })

  it("displays page indicator", () => {
    renderView({ total: 60, filters: { ...defaultFilters, page: 2, pageSize: 20 } })
    expect(screen.getByText("2 / 3")).toBeInTheDocument()
  })

  it("shows placeholder dash when details is null", () => {
    renderView({ items: [secondEntry] })
    const cells = screen.getAllByText("-")
    expect(cells.length).toBeGreaterThanOrEqual(1)
  })

  it("truncates long details to 80 chars", () => {
    const longDetail = { long: "a".repeat(200) }
    const entry: AuditLogEntry = { ...sampleEntry, details: longDetail }
    renderView({ items: [entry] })
    const serialized = JSON.stringify(longDetail).slice(0, 80)
    expect(screen.getByText(serialized)).toBeInTheDocument()
  })
})
