import { render, screen, fireEvent } from "@testing-library/react";
import { OnboardingProvider, useOnboarding } from "../onboarding/OnboardingProvider";
import { OnboardingChecklist } from "../onboarding/OnboardingChecklist";
import { TourProvider } from "../tour/TourProvider";

jest.mock("@salesos/ui", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports -- jest.mock factories can't reference outer-scope imports
  const h = require("react").createElement;
  return {
    cn: (...classes: any[]) => classes.filter(Boolean).join(" "),
    Card: (props: any) =>
      h("div", { ...props, "data-testid": "card", className: props.className }, props.children),
    CardHeader: (props: any) => h("div", { "data-testid": "card-header" }, props.children),
    CardContent: (props: any) => h("div", { "data-testid": "card-content" }, props.children),
    CardFooter: (props: any) => h("div", { "data-testid": "card-footer" }, props.children),
  };
});

describe("OnboardingProvider", () => {
  it("provides initial state with all items incomplete", () => {
    function Test() {
      const { items, completed, progress } = useOnboarding();
      return (
        <div>
          <div data-testid="item-count">{items.length}</div>
          <div data-testid="completed-count">{completed.length}</div>
          <div data-testid="progress">{progress}</div>
        </div>
      );
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>
    );
    expect(screen.getByTestId("item-count").textContent).toBe("6");
    expect(screen.getByTestId("completed-count").textContent).toBe("0");
    expect(screen.getByTestId("progress").textContent).toBe("0");
  });

  it("marks item as complete", () => {
    function Test() {
      const { completed, completeItem } = useOnboarding();
      return (
        <div>
          <div data-testid="completed-count">{completed.length}</div>
          <button data-testid="complete-btn" onClick={() => completeItem("profile")}>
            Complete
          </button>
        </div>
      );
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>
    );
    expect(screen.getByTestId("completed-count").textContent).toBe("0");
    fireEvent.click(screen.getByTestId("complete-btn"));
    expect(screen.getByTestId("completed-count").textContent).toBe("1");
  });

  it("does not duplicate completed items", () => {
    function Test() {
      const { completed, completeItem } = useOnboarding();
      return (
        <div>
          <div data-testid="completed-count">{completed.length}</div>
          <button
            data-testid="complete-btn"
            onClick={() => {
              completeItem("profile");
              completeItem("profile");
            }}
          >
            Complete
          </button>
        </div>
      );
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>
    );
    fireEvent.click(screen.getByTestId("complete-btn"));
    expect(screen.getByTestId("completed-count").textContent).toBe("1");
  });

  it("tracks completed items in memory", () => {
    // Provider is in-memory only — no localStorage persistence.
    function Test() {
      const { completed, completeItem } = useOnboarding();
      return (
        <div>
          <div data-testid="completed">{completed.join(",")}</div>
          <button onClick={() => completeItem("pipeline")}>Complete</button>
        </div>
      );
    }

    render(
      <OnboardingProvider>
        <Test />
      </OnboardingProvider>
    );
    fireEvent.click(screen.getByText("Complete"));
    expect(screen.getByTestId("completed").textContent).toBe("pipeline");
  });
});

describe("OnboardingChecklist", () => {
  it("renders checklist items", () => {
    render(
      <TourProvider>
        <OnboardingProvider>
          <OnboardingChecklist />
        </OnboardingProvider>
      </TourProvider>
    );
    expect(screen.getByText("أكمل ملفك الشخصي")).toBeInTheDocument();
    expect(screen.getByText("استورد خط الأنابيب")).toBeInTheDocument();
    expect(screen.getByText("أنشئ أول سير عمل")).toBeInTheDocument();
    expect(screen.getByText("ادعُ أعضاء الفريق")).toBeInTheDocument();
    expect(screen.getByText("اضبط التكاملات")).toBeInTheDocument();
    expect(screen.getByText("شغّل أول تحليل NBA")).toBeInTheDocument();
  });

  it("shows progress correctly", () => {
    function SeedProgress() {
      const { completeItem } = useOnboarding();
      return (
        <>
          <button
            type="button"
            onClick={() => {
              completeItem("profile");
              completeItem("pipeline");
            }}
          >
            seed
          </button>
          <OnboardingChecklist />
        </>
      );
    }

    render(
      <TourProvider>
        <OnboardingProvider>
          <SeedProgress />
        </OnboardingProvider>
      </TourProvider>
    );
    fireEvent.click(screen.getByText("seed"));
    expect(screen.getByText("2 / 6")).toBeInTheDocument();
  });

  it("renders nothing when all items are complete", () => {
    const ALL = ["profile", "pipeline", "workflow", "team", "integrations", "nba"];

    function SeedComplete() {
      const { completeItem } = useOnboarding();
      return (
        <>
          <button type="button" onClick={() => ALL.forEach((id) => completeItem(id))}>
            seed-all
          </button>
          <OnboardingChecklist />
        </>
      );
    }

    render(
      <TourProvider>
        <OnboardingProvider>
          <SeedComplete />
        </OnboardingProvider>
      </TourProvider>
    );
    fireEvent.click(screen.getByText("seed-all"));
    expect(screen.queryByText("البدء مع SalesOS")).not.toBeInTheDocument();
  });
});
