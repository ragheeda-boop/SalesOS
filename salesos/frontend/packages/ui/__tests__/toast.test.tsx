import { render, screen } from "@testing-library/react";
import { Toast, ToastViewport } from "../src/toast";

describe("Toast", () => {
  it("renders with title and description under ToastViewport alone", () => {
    render(
      <ToastViewport>
        <Toast title="Success" description="Operation completed" />
      </ToastViewport>
    );
    expect(screen.getByText("Success")).toBeInTheDocument();
    expect(screen.getByText("Operation completed")).toBeInTheDocument();
  });
});
