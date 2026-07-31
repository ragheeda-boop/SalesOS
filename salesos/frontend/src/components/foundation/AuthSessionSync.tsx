"use client";

import { useEffect } from "react";
import { syncAccessTokenCookieFromStorage } from "@/lib/auth/session";

/** Keeps the access_token cookie aligned with localStorage for edge middleware. */
export function AuthSessionSync() {
  useEffect(() => {
    syncAccessTokenCookieFromStorage();
  }, []);

  return null;
}
