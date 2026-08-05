// Workspace-specific testing utilities
export { TelemetrySpy, createTelemetrySpy } from "./mockTelemetry";
export type { MockWidgetContext, MockFactory } from "./types";

// Re-exported from canonical SDK for convenience
export {
  describeWidgetContract,
  renderWidget,
  createMockWidget,
} from "@salesos/widget-sdk/testing";
export { mockPermissionsAll, mockPermissionsNone } from "@salesos/widget-sdk/testing";
export { mockFeatureFlagsAll, mockFeatureFlagsNone } from "@salesos/widget-sdk/testing";
