import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  TenantOwnerPlatformFields,
  buildOwnerPlatformWritePayload,
  fromDateInputValue,
  provisioningStatusLabel,
  provisioningStatusVariant,
  toDateInputValue,
} from "../TenantOwnerPlatformFields";

describe("TenantOwnerPlatformFields helpers", () => {
  it("defaults provisioning label/variant", () => {
    expect(provisioningStatusLabel(undefined)).toBe("pending");
    expect(provisioningStatusVariant("active")).toBe("success");
    expect(provisioningStatusVariant("failed")).toBe("danger");
  });

  it("round-trips date input values", () => {
    expect(toDateInputValue("2026-09-14T00:00:00.000Z")).toBe("2026-09-14");
    expect(fromDateInputValue("2026-09-14")).toBe("2026-09-14T00:00:00.000Z");
    expect(fromDateInputValue("")).toBeNull();
  });

  it("builds trimmed write payload", () => {
    expect(
      buildOwnerPlatformWritePayload({
        plan_id: "  plan-a  ",
        region: " ",
        data_residency: "ae",
        provisioning_status: "active",
        trial_ends_at: null,
      }),
    ).toEqual({
      plan_id: "plan-a",
      region: null,
      data_residency: "ae",
      provisioning_status: "active",
      trial_ends_at: null,
    });
  });
});

describe("TenantOwnerPlatformFields", () => {
  it("renders read-path placeholders", () => {
    render(
      <TenantOwnerPlatformFields
        tenant={{
          plan_id: null,
          region: null,
          data_residency: null,
          provisioning_status: "pending",
          trial_ends_at: null,
        }}
      />,
    );
    expect(screen.getByTestId("tenant-owner-platform-fields")).toBeInTheDocument();
    expect(screen.getByText("Owner Platform")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("renders values in read mode", () => {
    render(
      <TenantOwnerPlatformFields
        tenant={{
          plan_id: "cat-1",
          region: "me-central-1",
          data_residency: "ae",
          provisioning_status: "active",
          trial_ends_at: "2026-12-01T00:00:00.000Z",
        }}
      />,
    );
    expect(screen.getByText("cat-1")).toBeInTheDocument();
    expect(screen.getByText("me-central-1")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("saves write-path payload", async () => {
    const onSave = jest.fn().mockResolvedValue(undefined);
    render(
      <TenantOwnerPlatformFields
        editable
        onSave={onSave}
        tenant={{
          plan_id: "old",
          region: "us-east-1",
          data_residency: null,
          provisioning_status: "pending",
          trial_ends_at: null,
        }}
      />,
    );

    expect(screen.getByTestId("tenant-owner-platform-edit")).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText("opaque catalog id"), {
      target: { value: "new-plan" },
    });
    fireEvent.change(screen.getByPlaceholderText("me-central-1"), {
      target: { value: "me-central-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Save Owner Platform/i }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          plan_id: "new-plan",
          region: "me-central-1",
          provisioning_status: "pending",
        }),
      );
    });
  });
});
