"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { getTenantId } from "./hooks/useTenant";

export interface CopilotToolTelemetry {
  tool_name: string;
  total_calls: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  avg_result_count: number;
}

export interface CopilotTelemetryLatencyBucket {
  label: string;
  p50: number;
  p95: number;
  p99: number;
}

export interface CopilotTelemetryResultBucket {
  label: string;
  count: number;
}

export interface CopilotTelemetryVolumePoint {
  date: string;
  calls: number;
  successes: number;
  failures: number;
}

export interface CopilotTelemetryResponse {
  summary: {
    total_calls: number;
    success_rate: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
  };
  tools: CopilotToolTelemetry[];
  latency_distribution: CopilotTelemetryLatencyBucket[];
  result_histogram: CopilotTelemetryResultBucket[];
  volume_over_time: CopilotTelemetryVolumePoint[];
}

export interface CopilotFeedbackPayload {
  message_id: string;
  conversation_id: string;
  rating: "positive" | "negative";
  comment?: string;
}

export interface CopilotFeedbackSummary {
  message_id: string;
  positive_count: number;
  negative_count: number;
  total_count: number;
  helpful_rate: number;
}

export const copilotKeys = {
  all: ["copilot"] as const,
  telemetry: (days: number) => [...copilotKeys.all, "telemetry", days] as const,
  feedback: (messageId: string) => [...copilotKeys.all, "feedback", messageId] as const,
};

export function useCopilotTelemetry(days = 7) {
  return useQuery({
    queryKey: copilotKeys.telemetry(days),
    queryFn: async () => {
      const res = await api.get("/api/v1/copilot/telemetry", {
        params: { days },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as CopilotTelemetryResponse;
    },
    refetchInterval: 60_000,
  });
}
