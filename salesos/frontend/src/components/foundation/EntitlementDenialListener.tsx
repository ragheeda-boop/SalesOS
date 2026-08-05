"use client";

import { useEffect } from "react";
import { useToast } from "@salesos/ui";
import {
  ENTITLEMENT_DENIED_EVENT,
  type EntitlementDeniedPayload,
} from "@/lib/api/entitlementErrors";
import { QUOTA_EXCEEDED_EVENT, type QuotaExceededPayload } from "@/lib/api/quotaErrors";
import { OWNER_AUTH_DENIED_EVENT } from "@/lib/auth/ownerAudience";

/**
 * STORY-06-02 / FE-S06-03b / FE-S07-06 — toast honest messaging for
 * entitlement 403s, quota_exceeded 403/429s, and owner-audience 401s.
 */
export function EntitlementDenialListener() {
  const { toast } = useToast();

  useEffect(() => {
    const onDenied = (event: Event) => {
      const detail = (event as CustomEvent<EntitlementDeniedPayload & { message?: string }>).detail;
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
        event as CustomEvent<QuotaExceededPayload & { message?: string; status?: number }>
      ).detail;
      if (!detail) return;
      const metric = detail.metric || "quota";
      toast({
        variant: "warning",
        title: metric === "ai_tokens" ? "AI token quota exceeded" : "Plan quota exceeded",
        description:
          detail.message ||
          `Quota exceeded for ${metric}. Upgrade plan or reduce usage. Not Production GO.`,
        duration: 8000,
      });
    };
    const onOwnerAuth = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string }>).detail;
      toast({
        variant: "warning",
        title: "Owner audience required",
        description:
          detail?.message ||
          "Admin APIs require salesos-owner-platform JWT. Owner login mint is DEC-093 follow-up. Not Production GO.",
        duration: 8000,
      });
    };
    window.addEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
    window.addEventListener(QUOTA_EXCEEDED_EVENT, onQuota);
    window.addEventListener(OWNER_AUTH_DENIED_EVENT, onOwnerAuth);
    return () => {
      window.removeEventListener(ENTITLEMENT_DENIED_EVENT, onDenied);
      window.removeEventListener(QUOTA_EXCEEDED_EVENT, onQuota);
      window.removeEventListener(OWNER_AUTH_DENIED_EVENT, onOwnerAuth);
    };
  }, [toast]);

  return null;
}
