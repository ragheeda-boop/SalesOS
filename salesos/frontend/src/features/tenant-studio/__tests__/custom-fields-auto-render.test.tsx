import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CustomFieldsAutoRender } from "../CustomFieldsAutoRender";

const mutate = jest.fn();

jest.mock("@/lib/hooks/tenantStudioQueries", () => ({
  useCustomFieldsFormSchema: () => ({
    data: {
      id: "custom-fields:company:v1",
      title: "Custom fields (company)",
      fields: [
        {
          key: "segment_tier",
          type: "enum",
          label: "Segment",
          enum: [
            { label: "A", value: "A" },
            { label: "B", value: "B" },
          ],
          section: "custom_fields",
        },
        {
          key: "renewal_date",
          type: "date",
          label: "Renewal",
          section: "custom_fields",
        },
      ],
      object_key: "company",
      tenant_id: "t1",
      schema_version: 1,
      values: {},
      bag_key: "custom_fields",
      renderer: "custom_fields_auto",
    },
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch: jest.fn(),
  }),
  useProjectCustomFieldValues: () => ({
    mutate,
    isPending: false,
  }),
}));

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: Record<string, unknown>) =>
    createElement("button", { type: "button", ...props }, children),
  Input: ({ label, ...props }: Record<string, unknown>) =>
    createElement("label", null, label, createElement("input", props)),
  Spinner: () => createElement("div", { "data-testid": "spinner" }),
  useToast: () => ({ toast: jest.fn() }),
}));

describe("CustomFieldsAutoRender — FE-S10-02", () => {
  it("renders tip form-schema fields generically", () => {
    render(<CustomFieldsAutoRender objectKey="company" />);
    expect(screen.getByTestId("custom-fields-auto-render")).toBeInTheDocument();
    expect(screen.getByTestId("custom-fields-auto-honesty")).toHaveTextContent(
      /form-schema/,
    );
    expect(
      screen.getByTestId("custom-fields-auto-input-segment_tier"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("custom-fields-auto-input-renewal_date"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("custom-fields-auto-meta")).toHaveTextContent(
      /custom_fields_auto/,
    );
  });

  it("projects tip POST .../values payload", async () => {
    render(<CustomFieldsAutoRender objectKey="company" />);
    fireEvent.change(
      screen.getByTestId("custom-fields-auto-input-segment_tier"),
      {
        target: { value: "A" },
      },
    );
    fireEvent.click(screen.getByTestId("custom-fields-auto-project"));
    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith(
        expect.objectContaining({
          values: expect.objectContaining({ segment_tier: "A" }),
        }),
        expect.any(Object),
      );
    });
  });
});
