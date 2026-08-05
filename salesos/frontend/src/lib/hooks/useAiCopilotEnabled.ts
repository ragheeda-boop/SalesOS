"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

/**
 * GA honesty: Copilot requires BOTH env opt-in AND backend evidence validation.
 *
 * Activation gates (both must pass):
 * 1. NEXT_PUBLIC_FEATURE_AI_COPILOT=true in runtime env (.env / .env.local)
 * 2. Backend /api/v1/copilot/status returns feature_ai_copilot: true
 *
 * If either gate fails, the copilot stays disabled.
 * See docs/audit/ga-engineering-audit/AI_HONESTY.md
 * See docs/ops/AI_COPILOT_ACTIVATION.md for full activation guide.
 */
export function useAiCopilotEnabled(): { enabled: boolean; ready: boolean } {
  const envEnabled = process.env.NEXT_PUBLIC_FEATURE_AI_COPILOT === "true";
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(!envEnabled);

  useEffect(() => {
    if (!envEnabled) {
      setEnabled(false);
      setReady(true);
      return;
    }
    let cancelled = false;
    api
      .get("/api/v1/copilot/status")
      .then((res) => {
        if (cancelled) return;
        setEnabled(res.data?.feature_ai_copilot === true);
        setReady(true);
      })
      .catch(() => {
        if (cancelled) return;
        setEnabled(false);
        setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [envEnabled]);

  return { enabled, ready };
}
