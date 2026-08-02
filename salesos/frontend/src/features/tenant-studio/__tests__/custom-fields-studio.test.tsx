import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CustomFieldsStudio } from "../CustomFieldsStudio";

const refetch = jest.fn();
const mutate = jest.fn();

jest.mock("@/lib/hooks/tenantStudioQueries", () => ({
  useCustomFieldSchema: () => ({
    data: {
      tenant_id: "t1",
      object_key: "company",
      schema_version: 2,
      fields: [
        {
          id: "f1",
          tenant_id: "t1",
          object_key: "company",
          field_key: "renewal_notes",
          field_type: "string",
          label: "Renewal notes",
          schema_version: 2,
          enum_values: [],
        },
      ],
    },
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useCreateCustomField: () => ({
    mutate,
    isPending: false,
  }),
}));

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: Record<string, unknown>) =>
    createElement("button", props, children),
  Input: ({ label, ...props }: Record<string, unknown>) =>
    createElement(
      "label",
      null,
      label,
      createElement("input", props),
    ),
  Spinner: () => createElement("div", { "data-testid": "spinner" }),
  useToast: () => ({ toast: jest.fn() }),
}));

describe("CustomFieldsStudio — FE-S10-01", () => {
  it("lists tip schema fields and shows in-memory honesty", () => {
    render(<CustomFieldsStudio />);
    expect(
      screen.getByTestId("custom-fields-studio-honesty"),
    ).toHaveTextContent(/in-memory/i);
    expect(screen.getByTestId("custom-fields-schema-meta")).toHaveTextContent(
      /schema_version\s*2/,
    );
    expect(screen.getByTestId("custom-fields-row")).toHaveTextContent(
      "renewal_notes",
    );
  });

  it("submits tip POST define payload", async () => {
    render(<CustomFieldsStudio />);
    fireEvent.change(screen.getByTestId("custom-fields-field-key"), {
      target: { value: "vip_tier" },
    });
    fireEvent.change(screen.getByTestId("custom-fields-field-type"), {
      target: { value: "enum" },
    });
    fireEvent.change(screen.getByTestId("custom-fields-enum-values"), {
      target: { value: "gold, silver" },
    });
    fireEvent.click(screen.getByTestId("custom-fields-submit"));
    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith(
        expect.objectContaining({
          object_key: "company",
          field_key: "vip_tier",
          field_type: "enum",
          enum_values: ["gold", "silver"],
        }),
        expect.any(Object),
      );
    });
  });
});
