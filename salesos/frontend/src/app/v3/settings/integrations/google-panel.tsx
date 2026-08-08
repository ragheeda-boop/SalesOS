"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import client from "@/lib/api/client";
import { contactKeys, dashboardKeys, employeeKeys } from "@/lib/queryKeys";

interface GoogleAccount {
  id: string;
  email: string;
  provider: string;
  is_active: boolean;
  scope: string | null;
  avatar_url: string | null;
  created_at: string;
  last_sync_at: string | null;
  token_expiry: string | null;
}

interface GoogleStatus {
  connected: boolean;
  account: GoogleAccount | null;
  scopes_granted: string[];
  token_valid: boolean;
  oauth_configured?: boolean;
  config_missing?: string[];
}

interface Props {
  ready: boolean;
  hasToken: boolean;
}

function readOauthReturnParams(): {
  google: string | null;
  email: string | null;
  reason: string | null;
  sync: string | null;
} {
  if (typeof window === "undefined") {
    return { google: null, email: null, reason: null, sync: null };
  }
  const params = new URLSearchParams(window.location.search);
  return {
    google: params.get("google"),
    email: params.get("email"),
    reason: params.get("reason"),
    sync: params.get("sync"),
  };
}

/** Strip OAuth return params so success/error banners are one-shot (not sticky in the URL). */
function clearOauthReturnParams(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  ["google", "email", "reason", "sync", "tab"].forEach((k) => url.searchParams.delete(k));
  window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
}

/** After Google sync, Emp360 / Company360 / contacts / dashboard must refetch. */
function invalidatePostSync(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: employeeKeys.all });
  void queryClient.invalidateQueries({ queryKey: ["company360"] });
  void queryClient.invalidateQueries({ queryKey: contactKeys.all });
  void queryClient.invalidateQueries({ queryKey: dashboardKeys.stats() });
  void queryClient.invalidateQueries({ queryKey: dashboardKeys.exec() });
  void queryClient.invalidateQueries({ queryKey: dashboardKeys.main() });
}

/** Prefer string API detail; avoid "[object Object]" for entitlement payloads. */
function extractApiDetail(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: { detail?: unknown; message?: string } } })?.response
    ?.data;
  const detail = data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (detail && typeof detail === "object") {
    const nested =
      (detail as { message?: string; detail?: string }).message ||
      (detail as { detail?: string }).detail;
    if (typeof nested === "string" && nested.trim()) return nested;
    try {
      return JSON.stringify(detail);
    } catch {
      /* fall through */
    }
  }
  if (typeof data?.message === "string" && data.message.trim()) return data.message;
  return fallback;
}

export function GoogleIntegrationPanel({ ready, hasToken }: Props) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [syncingGmail, setSyncingGmail] = useState(false);
  const [syncingCalendar, setSyncingCalendar] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const autoSyncStarted = useRef(false);

  const fetchStatus = useCallback(async () => {
    if (!ready || !hasToken) return;
    setLoading(true);
    try {
      const res = await client.get<GoogleStatus>("/api/v1/integrations/google/status");
      setStatus(res.data);
    } catch (err) {
      console.warn("[GooglePanel] status fetch failed", err);
      setStatus({
        connected: false,
        account: null,
        scopes_granted: [],
        token_valid: false,
      });
    } finally {
      setLoading(false);
    }
  }, [ready, hasToken]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const runFirstSync = useCallback(async () => {
    setSyncingGmail(true);
    setSyncingCalendar(true);
    setError(null);
    setSyncMessage("Starting first Gmail + Calendar sync…");
    try {
      const [gmailRes, calRes] = await Promise.allSettled([
        client.post<{ message: string; errors?: string[] }>("/api/v1/integrations/google/sync", {
          days_lookback: 30,
          max_results: 100,
        }),
        client.post<{ message: string; errors?: string[] }>(
          "/api/v1/integrations/google/calendar-sync",
          { days_lookback: 90, days_forward: 90 }
        ),
      ]);
      const parts: string[] = [];
      if (gmailRes.status === "fulfilled") {
        parts.push(gmailRes.value.data.message || "Gmail synced");
      } else {
        parts.push("Gmail sync failed");
      }
      if (calRes.status === "fulfilled") {
        parts.push(calRes.value.data.message || "Calendar synced");
      } else {
        parts.push("Calendar sync failed");
      }
      setSyncMessage(parts.join(" · "));
      if (gmailRes.status === "rejected" && calRes.status === "rejected") {
        setError("First sync failed — use Sync Gmail / Sync Calendar to retry");
      }
      invalidatePostSync(queryClient);
      await fetchStatus();
    } finally {
      setSyncingGmail(false);
      setSyncingCalendar(false);
    }
  }, [fetchStatus, queryClient]);

  useEffect(() => {
    const { google, email, reason, sync } = readOauthReturnParams();
    if (!google) return;
    if (google === "connected") {
      setSyncMessage(
        email
          ? `Google connected as ${email}${sync === "started" ? " — first sync started" : ""}`
          : "Google account connected successfully"
      );
      setError(null);
      void fetchStatus().then(() => {
        // Belt-and-suspenders with backend schedule_initial_sync — once per return.
        if (!autoSyncStarted.current && ready && hasToken) {
          autoSyncStarted.current = true;
          void runFirstSync();
        }
      });
      clearOauthReturnParams();
    } else if (google === "error") {
      setError(`Google connection failed (${reason || "unknown"})`);
      clearOauthReturnParams();
    } else {
      // Unknown google=* return — still strip so params never stick forever.
      clearOauthReturnParams();
    }
  }, [fetchStatus, ready, hasToken, runFirstSync]);

  const handleConnect = useCallback(async () => {
    setConnecting(true);
    setError(null);
    try {
      const res = await client.get<{
        authorization_url: string;
        state: string;
      }>("/api/v1/integrations/google/connect");
      window.location.href = res.data.authorization_url;
    } catch {
      setError("Failed to initiate Google connection");
      setConnecting(false);
    }
  }, []);

  const handleDisconnect = useCallback(async () => {
    setDisconnecting(true);
    setError(null);
    setSyncMessage(null);
    try {
      await client.post("/api/v1/integrations/google/disconnect");
      await fetchStatus();
    } catch {
      setError("Failed to disconnect Google account");
    } finally {
      setDisconnecting(false);
    }
  }, [fetchStatus]);

  const handleSyncGmail = useCallback(async () => {
    console.warn("[GooglePanel] handleSyncGmail fired");
    // Immediate UI proof the handler ran (before network / CSRF mint).
    setSyncingGmail(true);
    setError(null);
    setSyncMessage("Syncing Gmail…");
    try {
      const res = await client.post<{ message: string; errors?: string[] }>(
        "/api/v1/integrations/google/sync",
        { days_lookback: 30, max_results: 100 }
      );
      const errs = res.data.errors?.length ? ` (${res.data.errors.length} item errors)` : "";
      setSyncMessage((res.data.message || "Gmail sync completed") + errs);
      invalidatePostSync(queryClient);
      await fetchStatus();
    } catch (err: unknown) {
      setSyncMessage(null);
      setError(extractApiDetail(err, "Gmail sync failed — check connection and try again"));
    } finally {
      setSyncingGmail(false);
    }
  }, [fetchStatus, queryClient]);

  const handleSyncCalendar = useCallback(async () => {
    console.warn("[GooglePanel] handleSyncCalendar fired");
    // Immediate UI proof the handler ran (before network / CSRF mint).
    setSyncingCalendar(true);
    setError(null);
    setSyncMessage("Syncing Calendar…");
    try {
      const res = await client.post<{ message: string; errors?: string[] }>(
        "/api/v1/integrations/google/calendar-sync",
        { days_lookback: 90, days_forward: 90 }
      );
      const errs = res.data.errors?.length ? ` (${res.data.errors.length} item errors)` : "";
      setSyncMessage((res.data.message || "Calendar sync completed") + errs);
      invalidatePostSync(queryClient);
      await fetchStatus();
    } catch (err: unknown) {
      setSyncMessage(null);
      setError(extractApiDetail(err, "Calendar sync failed — check connection and try again"));
    } finally {
      setSyncingCalendar(false);
    }
  }, [fetchStatus, queryClient]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)] py-4">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--border-default)] border-t-transparent" />
        Loading connection status...
      </div>
    );
  }

  const connected = status?.connected && status?.account;
  const canSync = Boolean(connected);
  const tokenValid = status?.token_valid ?? false;

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-[var(--radius-md)] border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="rounded-[var(--radius-md)] border border-[var(--border-default)] p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-white shadow-sm">
              <svg viewBox="0 0 24 24" className="h-6 w-6">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-medium text-[var(--text-primary)]">Google Workspace</h3>
              <p className="text-xs text-[var(--text-secondary)]">Gmail and Calendar sync</p>
            </div>
          </div>

          {connected ? (
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  tokenValid
                    ? "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
                    : "bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300"
                }`}
              >
                {tokenValid ? "Connected" : "Needs Reconnect"}
              </span>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] disabled:opacity-50"
              >
                {disconnecting ? "Disconnecting..." : "Disconnect"}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleConnect}
              disabled={connecting}
              className="rounded-[var(--radius-md)] bg-blue-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {connecting ? "Connecting..." : "Connect Google"}
            </button>
          )}
        </div>

        {connected && status?.account && (
          <div className="mt-3 border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-secondary)]">
            <div className="flex items-center gap-2">
              {status.account.avatar_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={status.account.avatar_url} alt="" className="h-5 w-5 rounded-full" />
              )}
              <span>{status.account.email}</span>
            </div>
            {status.account.last_sync_at && (
              <p className="mt-1">
                Last sync: {new Date(status.account.last_sync_at).toLocaleString()}
              </p>
            )}
            {status.scopes_granted.length > 0 && (
              <p className="mt-1">Scopes: {status.scopes_granted.length} permissions granted</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                data-testid="google-sync-gmail"
                aria-busy={syncingGmail}
                onClick={() => void handleSyncGmail()}
                disabled={syncingGmail || syncingCalendar || !canSync}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] disabled:opacity-50"
              >
                {syncingGmail ? "Syncing Gmail..." : "Sync Gmail"}
              </button>
              <button
                type="button"
                data-testid="google-sync-calendar"
                aria-busy={syncingCalendar}
                onClick={() => void handleSyncCalendar()}
                disabled={syncingCalendar || syncingGmail || !canSync}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] disabled:opacity-50"
              >
                {syncingCalendar ? "Syncing Calendar..." : "Sync Calendar"}
              </button>
            </div>
            {(syncMessage || syncingGmail || syncingCalendar) && (
              <p
                role="status"
                aria-live="polite"
                data-testid="google-sync-status"
                className="mt-2 text-green-700 dark:text-green-300"
              >
                {syncMessage ||
                  (syncingGmail ? "Syncing Gmail…" : syncingCalendar ? "Syncing Calendar…" : null)}
              </p>
            )}
          </div>
        )}

        {!connected && (
          <div className="mt-3 space-y-1 border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-secondary)]">
            <p>
              Not connected — Employee360 email/calendar and Communication Hub stay empty until you
              connect. Nothing is invented while disconnected.
            </p>
            {status?.oauth_configured === false && (
              <p
                className="text-amber-700 dark:text-amber-300"
                data-testid="google-oauth-config-gap"
              >
                Google OAuth is not configured on this environment
                {status.config_missing?.length
                  ? ` (missing: ${status.config_missing.join(", ")})`
                  : ""}
                . Connect returns 503 until credentials are set; Sync buttons appear only after a
                successful connect.
              </p>
            )}
            <p>
              Connect Google to enable Gmail and Calendar sync. First sync starts automatically
              after consent; tokens are encrypted at rest.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
