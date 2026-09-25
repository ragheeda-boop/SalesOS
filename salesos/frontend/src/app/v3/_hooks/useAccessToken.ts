"use client";

import { useEffect, useState } from "react";
import { classifyJwtAudience, type JwtAudienceKind } from "@/lib/auth/ownerAudience";

/**
 * Detects legacy-compatible auth (localStorage access_token).
 * Avoids firing company API calls until we know whether to show a login CTA.
 */
export function useAccessToken(): {
  ready: boolean;
  hasToken: boolean;
  audienceKind: JwtAudienceKind;
} {
  const [ready, setReady] = useState(false);
  const [hasToken, setHasToken] = useState(false);
  const [audienceKind, setAudienceKind] = useState<JwtAudienceKind>("missing");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setHasToken(!!token);
    setAudienceKind(classifyJwtAudience(token));
    setReady(true);
  }, []);

  return { ready, hasToken, audienceKind };
}
