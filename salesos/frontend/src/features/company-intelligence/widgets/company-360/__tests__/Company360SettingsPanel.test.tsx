import { render, screen } from "@testing-library/react";
import { Company360SettingsPanel } from "../Company360SettingsPanel";

describe("Company360SettingsPanel", () => {
  it("renders mapped company360 fields", () => {
    render(
      <Company360SettingsPanel
        company360={{
          company: { name_ar: "شركة الاختبار", tags: ["vip"], status: "active" },
          assigned_employees: [{ full_name: "أحمد" }],
        }}
      />
    );
    const panel = screen.getByTestId("company360-settings-panel");
    expect(panel).toHaveTextContent("شركة الاختبار");
    expect(panel).toHaveTextContent("vip");
    expect(panel).toHaveTextContent("أحمد");
    expect(screen.queryByText("إعدادات الشركة")).not.toBeInTheDocument();
  });

  it("shows honest empty when no company fields exist", () => {
    render(<Company360SettingsPanel company360={{}} />);
    expect(screen.getByText("لا توجد بيانات إعدادات")).toBeInTheDocument();
    expect(screen.queryByTestId("company360-settings-panel")).not.toBeInTheDocument();
  });
});
