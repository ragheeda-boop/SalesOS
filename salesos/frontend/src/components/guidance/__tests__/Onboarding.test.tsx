import { render, screen, fireEvent } from "@testing-library/react"
import { OnboardingProvider, useOnboarding } from "../onboarding/OnboardingProvider"
import { OnboardingChecklist } from "../onboarding/OnboardingChecklist"
import { TourProvider } from "../tour/TourProvider"
import { Card } from "@/components/foundation/card"

jest.mock("@/components/foundation/card", () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
}))

describe("OnboardingProvider", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("provides initial state with all items incomplete", () => {
    function Test() {
      const { items, completed, progress } = useOnboarding()
      return (
        <div>
          <div data-testid="item-count">{items.length}</div>
          <div data-testid="completed-count">{completed.length}</div>
          <div data-testid="progress">{progress}</div>
        </div>
      )
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>,
    )
    expect(screen.getByTestId("item-count").textContent).toBe("6")
    expect(screen.getByTestId("completed-count").textContent).toBe("0")
    expect(screen.getByTestId("progress").textContent).toBe("0")
  })

  it("marks item as complete", () => {
    function Test() {
      const { completed, completeItem } = useOnboarding()
      return (
        <div>
          <div data-testid="completed-count">{completed.length}</div>
          <button data-testid="complete-btn" onClick={() => completeItem("profile")}>Complete</button>
        </div>
      )
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>,
    )
    expect(screen.getByTestId("completed-count").textContent).toBe("0")
    fireEvent.click(screen.getByTestId("complete-btn"))
    expect(screen.getByTestId("completed-count").textContent).toBe("1")
  })

  it("does not duplicate completed items", () => {
    function Test() {
      const { completed, completeItem } = useOnboarding()
      return (
        <div>
          <div data-testid="completed-count">{completed.length}</div>
          <button data-testid="complete-btn" onClick={() => { completeItem("profile"); completeItem("profile") }}>Complete</button>
        </div>
      )
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>,
    )
    fireEvent.click(screen.getByTestId("complete-btn"))
    expect(screen.getByTestId("completed-count").textContent).toBe("1")
  })

  it("persists completed items to localStorage", () => {
    function Test() {
      const { completeItem } = useOnboarding()
      return (
        <div>
          <button onClick={() => completeItem("pipeline")}>Complete</button>
        </div>
      )
    }

    const { unmount } = render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>,
    )
    fireEvent.click(screen.getByText("Complete"))
    unmount()

    const stored = JSON.parse(localStorage.getItem("salesos:onboarding-progress") || "[]")
    expect(stored).toEqual(["pipeline"])
  })
})

describe("OnboardingChecklist", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("renders checklist items", () => {
    render(
      <TourProvider>
        <OnboardingProvider>
          <OnboardingChecklist />
        </OnboardingProvider>
      </TourProvider>,
    )
    expect(screen.getByText("أكمل ملفك الشخصي")).toBeInTheDocument()
    expect(screen.getByText("استورد خط الأنابيب")).toBeInTheDocument()
    expect(screen.getByText("أنشئ أول سير عمل")).toBeInTheDocument()
    expect(screen.getByText("ادعُ أعضاء الفريق")).toBeInTheDocument()
    expect(screen.getByText("اضبط التكاملات")).toBeInTheDocument()
    expect(screen.getByText("شغّل أول تحليل NBA")).toBeInTheDocument()
  })

  it("shows progress correctly", () => {
    localStorage.setItem("salesos:onboarding-progress", JSON.stringify(["profile", "pipeline"]))

    render(
      <TourProvider>
        <OnboardingProvider>
          <OnboardingChecklist />
        </OnboardingProvider>
      </TourProvider>,
    )
    expect(screen.getByText("2 / 6")).toBeInTheDocument()
  })

  it("renders nothing when all items are complete", () => {
    localStorage.setItem(
      "salesos:onboarding-progress",
      JSON.stringify(["profile", "pipeline", "workflow", "team", "integrations", "nba"]),
    )

    render(
      <TourProvider>
        <OnboardingProvider>
          <OnboardingChecklist />
        </OnboardingProvider>
      </TourProvider>,
    )
    expect(screen.queryByText("البدء مع SalesOS")).not.toBeInTheDocument()
  })
})
