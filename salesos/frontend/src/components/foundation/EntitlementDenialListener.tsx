"use client";

import { useEffect } from "react";
import { useToast } from "@salesos/ui";
import {
  ENTITLEMENT_DENIED_EVENT,
  type EntitlementDeniedPayload,
} from "@/lib/api/entitlementErrors";
import {
  QUOTA_EXCEEDED_EVENT,
  type QuotaExceededPayload,
} from "@/lib/api/quotaErrors";

/**
 * STORY-06-02 / FE-S06-03b — toast honest upgrade messaging on
 * entitlement 403s and quota_exceeded 403/429s from the API client.
 */
export function EntitlementDenialListener() {
  const { toast } = useToast();

  useEffect(() => {
    const onDenied = (event: Event) => {
      const detail = (
        event as CustomEvent<EntitlementDeniedPayload & { message?: string }>
      ).detail;
      if (!detail) return;
      toast({
        variant: "warning",
        title: "Plan upgrade required",
        description:
          detail.message ||
          `Domain ${detail.domain || "gated"} is not entitled on the current plan. Upgrade or ask Owner to edit Plan.entitlements. Not Production GO.`,
        duration: 8000,
      });
    };
    const onQuota = (event: Event) => {
      const detail = (
        event as CustomEvent<
          QuotaExceededPayload & { message?: string; status?: number }
        >
      ).detail;
      if (!detail) return;
      const metric = detail.metric || "quota";
      toast({
        variant: "warning",
        title:
          metric === "ai_tokens"
            ? "AI token quota exceeded"
            : "Plan quota exceeded",
        description:
          detail.message ||
          `Quota exceeded for ${metric}. Upgrade plan or reduce usage. Not Production GO.`,
        duration: 8000,
      });
    };
    window.addEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
    window.addEventListener(QUOTA_EXCEEDED_EVENT, onQuota);
    return () => {
      window.removeEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
      window.removeEventListener(QUOTA_EXCEEDED_EVENT, onQuota);
    };
  }, [toast]);

  return null;
}
