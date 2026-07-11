import { render, screen, fireEvent, act } from "@testing-library/react"
import { TourProvider, useTour } from "../tour/TourProvider"
import { TourOverlay } from "../tour/TourOverlay"
import type { TourStep } from "../tour/TourStep"

const MOCK_STEPS: TourStep[] = [
  { target: "", title: "Step 1", description: "First step", position: "center" },
  { target: "", title: "Step 2", description: "Second step", position: "center" },
  { target: "", title: "Step 3", description: "Third step", position: "center" },
]

function TestHarness() {
  const { startTour, isActive, currentStep, nextStep, prevStep, endTour, shouldShowTour, markTourCompleted } = useTour()

  return (
    <div>
      <div data-testid="is-active">{String(isActive)}</div>
      <div data-testid="current-step">{currentStep}</div>
      <button data-testid="start-tour" onClick={() => startTour("test", MOCK_STEPS)}>
        Start
      </button>
      <button data-testid="next" onClick={nextStep}>Next</button>
      <button data-testid="prev" onClick={prevStep}>Prev</button>
      <button data-testid="end" onClick={endTour}>End</button>
      <button data-testid="mark-completed" onClick={() => markTourCompleted("test")}>Mark Complete</button>
      <div data-testid="should-show">{String(shouldShowTour("test"))}</div>
      <TourOverlay />
    </div>
  )
}

function renderHarness() {
  return render(
    <TourProvider>
      <TestHarness />
    </TourProvider>,
  )
}

describe("Tour", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("provides context with initial state", () => {
    renderHarness()
    expect(screen.getByTestId("is-active").textContent).toBe("false")
    expect(screen.getByTestId("current-step").textContent).toBe("0")
  })

  it("starts a tour", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    expect(screen.getByTestId("is-active").textContent).toBe("true")
    expect(screen.getByText("Step 1")).toBeInTheDocument()
  })

  it("navigates to next step", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    fireEvent.click(screen.getByText("التالي"))
    expect(screen.getByText("Step 2")).toBeInTheDocument()
  })

  it("navigates to previous step", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    fireEvent.click(screen.getByText("التالي"))
    fireEvent.click(screen.getByText("السابق"))
    expect(screen.getByText("Step 1")).toBeInTheDocument()
  })

  it("ends tour early", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    fireEvent.click(screen.getByTestId("end"))
    expect(screen.getByTestId("is-active").textContent).toBe("false")
  })

  it("marks tour completed and persists to localStorage", () => {
    renderHarness()
    expect(screen.getByTestId("should-show").textContent).toBe("true")
    fireEvent.click(screen.getByTestId("mark-completed"))
    const stored = JSON.parse(localStorage.getItem("salesos:completed-tours") || "[]")
    expect(stored).toContain("test")
  })

  it("shows step number in overlay", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    expect(screen.getByText("الخطوة 1 من 3")).toBeInTheDocument()
  })

  it("shows done button on last step", () => {
    renderHarness()
    fireEvent.click(screen.getByTestId("start-tour"))
    fireEvent.click(screen.getByText("التالي"))
    fireEvent.click(screen.getByText("التالي"))
    expect(screen.getByText("تم")).toBeInTheDocument()
  })
})
