import { createElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { PermissionsStudio } from "../PermissionsStudio";

const refetch = jest.fn();
const setCeilingMutate = jest.fn();
const upsertMutate = jest.fn();
const checkMutate = jest.fn();

jest.mock("@/lib/hooks/permissionsStudioQueries", () => ({
  usePermissionsCatalog: () => ({
    data: [
      {
        key: "crm.companies.read",
        name: "Read Companies",
        description: "View company records",
        domain: "DOM-001",
        group: "crm",
        requires_publish: false,
        within_ceiling: true,
        ceiling_reason: null,
      },
      {
        key: "ai.rag.use",
        name: "Use RAG",
        description: "AI",
        domain: "DOM-011",
        group: "ai",
        requires_publish: false,
        within_ceiling: false,
        ceiling_reason: "DOM-011 disabled",
      },
    ],
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  usePermissionsCeiling: () => ({
    data: {
      enabled_domains: ["DOM-001"],
      publish_domains: [],
      grantable_permissions: ["crm.companies.read"],
    },
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useCustomRoles: () => ({
    data: [
      {
        id: "role-1",
        tenant_id: "t1",
        name: "Seller",
        description: "",
        permissions: ["crm.companies.read"],
        schema_version: 1,
      },
    ],
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch,
  }),
  useSetPermissionsCeiling: () => ({
    mutate: setCeilingMutate,
    isPending: false,
  }),
  useUpsertCustomRole: () => ({
    mutate: upsertMutate,
    isPending: false,
  }),
  useCheckPermissionsCeiling: () => ({
    mutate: checkMutate,
    isPending: false,
    data: undefined,
  }),
}));

jest.mock("@salesos/ui", () => ({
  Button: ({ children, ...props }: Record<string, unknown>) =>
    createElement("button", props, children),
  Input: ({ label, ...props }: Record<string, unknown>) =>
    createElement("label", null, label, createElement("input", props)),
  Spinner: () => createElement("div", { "data-testid": "spinner" }),
  useToast: () => ({ toast: jest.fn() }),
}));

describe("PermissionsStudio — FE-S10-06", () => {
  it("lists catalog/roles and shows ceiling honesty", () => {
    render(<PermissionsStudio />);
    expect(screen.getByTestId("permissions-studio-honesty")).toHaveTextContent(/ceiling/i);
    expect(screen.getByTestId("permissions-studio-honesty")).toHaveTextContent(/in-memory/i);
    expect(screen.getByTestId("permissions-ceiling-meta")).toHaveTextContent(/grantable\s*1/);
    expect(screen.getByTestId("permissions-role-row")).toHaveTextContent("Seller");
    expect(screen.getByTestId("permissions-select-ai.rag.use")).toBeDisabled();
  });

  it("sets tip PUT ceiling", async () => {
    render(<PermissionsStudio />);
    fireEvent.click(screen.getByTestId("permissions-set-ceiling"));
    await waitFor(() => {
      expect(setCeilingMutate).toHaveBeenCalledWith(
        expect.objectContaining({ plan_tier: "starter" }),
        expect.any(Object)
      );
    });
  });

  it("submits tip POST custom role upsert", async () => {
    render(<PermissionsStudio />);
    fireEvent.click(screen.getByTestId("permissions-select-crm.companies.read"));
    fireEvent.change(screen.getByTestId("permissions-role-name"), {
      target: { value: "Closer" },
    });
    fireEvent.click(screen.getByTestId("permissions-role-submit"));
    await waitFor(() => {
      expect(upsertMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Closer",
          permissions: ["crm.companies.read"],
          plan_tier: "starter",
        }),
        expect.any(Object)
      );
    });
  });
});
