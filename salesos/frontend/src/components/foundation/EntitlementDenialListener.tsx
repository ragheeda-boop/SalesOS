"use client";

import { useEffect } from "react";
import { useToast } from "@salesos/ui";
import {
  ENTITLEMENT_DENIED_EVENT,
  type EntitlementDeniedPayload,
} from "@/lib/api/entitlementErrors";

/**
 * STORY-06-02 — toast honest upgrade messaging on entitlement 403s.
 * Listens for events dispatched by the API client interceptor.
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
    window.addEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
    return () => window.removeEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
  }, [toast]);

  return null;
}
