import type { WidgetStatus } from "@salesos/widget-sdk";

export function deriveStatus(data: unknown, isLoading: boolean, isError: boolean): WidgetStatus {
  if (isLoading && !data) return "loading";
  if (isLoading && data) return "degraded";
  if (isError && !data) return "error";
  if (isError && data) return "degraded";
  if (!data) return "loading";
  return "ready";
}
