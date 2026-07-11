import { render, screen, fireEvent } from "@testing-library/react"
import { TourProvider } from "../tour/TourProvider"
import { EmptyPipeline } from "../empty-states/EmptyPipeline"
import { EmptyNBA } from "../empty-states/EmptyNBA"
import { EmptyWorkflows } from "../empty-states/EmptyWorkflows"
import { EmptyRAG } from "../empty-states/EmptyRAG"
import { EmptyMeetings } from "../empty-states/EmptyMeetings"
import { EmptyAnalytics } from "../empty-states/EmptyAnalytics"
import { Book } from "lucide-react"
import { EmptyState } from "../empty-states/EmptyState"

function renderWithTour(ui: React.ReactElement) {
  return render(<TourProvider>{ui}</TourProvider>)
}

describe("EmptyState", () => {
  it("renders with basic props", () => {
    renderWithTour(
      <EmptyState
        icon={<Book data-testid="icon" />}
        title="No data"
        description="No data available yet."
      />,
    )
    expect(screen.getByText("No data")).toBeInTheDocument()
    expect(screen.getByText("No data available yet.")).toBeInTheDocument()
    expect(screen.getByTestId("icon")).toBeInTheDocument()
  })

  it("renders action button and fires onClick", () => {
    const handleClick = jest.fn()
    renderWithTour(
      <EmptyState
        icon={<Book />}
        title="No data"
        description="No data"
        action={{ label: "Create", onClick: handleClick }}
      />,
    )
    const btn = screen.getByText("Create")
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it("renders secondary action", () => {
    const handlePrimary = jest.fn()
    const handleSecondary = jest.fn()
    renderWithTour(
      <EmptyState
        icon={<Book />}
        title="No data"
        description="No data"
        action={{ label: "Primary", onClick: handlePrimary }}
        secondaryAction={{ label: "Secondary", onClick: handleSecondary }}
      />,
    )
    expect(screen.getByText("Primary")).toBeInTheDocument()
    expect(screen.getByText("Secondary")).toBeInTheDocument()
  })

  it("shows tour button when tourId is provided", () => {
    renderWithTour(
      <EmptyState
        icon={<Book />}
        title="No data"
        description="No data"
        tourId="pipeline"
      />,
    )
    expect(screen.getByText("جولة تعريفية")).toBeInTheDocument()
  })

  it("does not show tour button if tour already completed", () => {
    localStorage.setItem("salesos:completed-tours", JSON.stringify(["pipeline"]))
    renderWithTour(
      <EmptyState
        icon={<Book />}
        title="No data"
        description="No data"
        tourId="pipeline"
      />,
    )
    expect(screen.queryByText("جولة تعريفية")).not.toBeInTheDocument()
  })
})

describe("EmptyPipeline", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyPipeline />)
    expect(screen.getByText("لا توجد صفقات بعد")).toBeInTheDocument()
  })

  it("calls onCreateOpportunity when button clicked", () => {
    const fn = jest.fn()
    renderWithTour(<EmptyPipeline onCreateOpportunity={fn} />)
    fireEvent.click(screen.getByText("إنشاء فرصة جديدة"))
    expect(fn).toHaveBeenCalled()
  })
})

describe("EmptyNBA", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyNBA />)
    expect(screen.getByText("التوصيات بحاجة لبيانات")).toBeInTheDocument()
  })
})

describe("EmptyWorkflows", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyWorkflows />)
    expect(screen.getByText("لا توجد أتمتة بعد")).toBeInTheDocument()
  })
})

describe("EmptyRAG", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyRAG />)
    expect(screen.getByText("لم يتم استيراد مستندات بعد")).toBeInTheDocument()
  })
})

describe("EmptyMeetings", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyMeetings />)
    expect(screen.getByText("لا توجد اجتماعات مسجلة")).toBeInTheDocument()
  })
})

describe("EmptyAnalytics", () => {
  it("renders with correct message", () => {
    renderWithTour(<EmptyAnalytics />)
    expect(screen.getByText("بيانات غير كافية للتقارير")).toBeInTheDocument()
  })
})
