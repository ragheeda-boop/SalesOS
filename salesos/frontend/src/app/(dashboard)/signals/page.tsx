"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { Tabs, TabsList, Tab, TabsPanel, cn } from "@salesos/ui";
import { Radio, CheckCheck, Bell, BellOff, Filter } from "lucide-react";

interface SignalItem {
  id: string;
  name: string;
  ar_name: string;
  description: string;
  domain: string;
  category: string;
  severity: string;
  source: string;
  pack_id: string;
  priority: string;
  weight: number;
  created_at: string;
}

interface SignalEventItem {
  id: string;
  signal_id: string;
  company_id: string;
  data: Record<string, unknown>;
  detected_at: string;
  acknowledged: boolean;
}

interface SubscriptionItem {
  id: string;
  signal_id: string;
  company_id: string;
  channel: string;
  active: boolean;
  created_at: string;
}

type Tab = "marketplace" | "feed" | "subscriptions";

export default function SignalsPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("marketplace");
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [feed, setFeed] = useState<SignalEventItem[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domainFilter, setDomainFilter] = useState<string>("");
  const [subscribing, setSubscribing] = useState<string | null>(null);

  const signalApiBase = "/api/v1/signals";

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "marketplace") {
        const params = domainFilter ? { domain: domainFilter } : {};
        const res = await api.get(signalApiBase, { params });
        setSignals(res.data.signals || []);
      } else if (tab === "feed") {
        const res = await api.get(`${signalApiBase}/feed`, {
          params: { limit: 100 },
        });
        setFeed(res.data.events || []);
      } else if (tab === "subscriptions") {
        const res = await api.get(`${signalApiBase}/subscriptions`);
        setSubscriptions(res.data || []);
      }
    } catch {
      setError(t("error.server_error"));
    } finally {
      setLoading(false);
    }
  }, [tab, domainFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSubscribe = async (signalId: string) => {
    setSubscribing(signalId);
    try {
      await api.post(`${signalApiBase}/subscribe`, {
        signal_id: signalId,
        company_id: "all",
        channel: "in-app",
      });
      setSignals((prev) => prev.map((s) => (s.id === signalId ? s : s)));
    } catch {
      setError(t("error.server_error"));
    } finally {
      setSubscribing(null);
    }
  };

  const handleUnsubscribe = async (subId: string) => {
    try {
      await api.delete(`${signalApiBase}/subscribe/${subId}`);
      setSubscriptions((prev) => prev.filter((s) => s.id !== subId));
    } catch {
      setError(t("error.server_error"));
    }
  };

  const handleAcknowledge = async (eventId: string) => {
    try {
      await api.post(`${signalApiBase}/${eventId}/acknowledge`);
      setFeed((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, acknowledged: true } : e)),
      );
    } catch {
      setError(t("error.server_error"));
    }
  };

  const severityColor = (sev: string) => {
    switch (sev) {
      case "critical":
        return "bg-red-100 text-red-700";
      case "warning":
        return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
      default:
        return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
    }
  };

  const domains = [...new Set(signals.map((s) => s.domain))];

  if (loading)
    return (
      <div className="p-8 text-center text-[var(--text-muted)]">
        {t("common.loading")}
      </div>
    );

  return (
    <div className="p-6 space-y-6">
      <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t("nav.signals")}</h1>
          <TabsList>
            <Tab value="marketplace">
              <Radio className="inline h-4 w-4 ml-1" />
              {t("signals.marketplace")}
            </Tab>
            <Tab value="feed">
              <Bell className="inline h-4 w-4 ml-1" />
              {t("signals.feed")}
            </Tab>
            <Tab value="subscriptions">
              <CheckCheck className="inline h-4 w-4 ml-1" />
              {t("signals.subscriptions")}
            </Tab>
          </TabsList>
        </div>

        {error && (
          <div className="bg-[var(--status-danger-bg)] text-[var(--status-danger-text)] p-3 rounded-lg text-sm">
            {error}
            <button onClick={loadData} className="ml-2 underline">
              {t("error.retry")}
            </button>
          </div>
        )}

        <TabsPanel value="marketplace">
          <div className="space-y-4">
            {domains.length > 1 && (
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-[var(--text-disabled)]" />
                <select
                  value={domainFilter}
                  onChange={(e) => setDomainFilter(e.target.value)}
                  className="rounded-lg border px-3 py-1.5 text-sm bg-[var(--bg-primary)]"
                >
                  <option value="">{t("status.all")}</option>
                  {domains.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {signals.length === 0 && (
              <p className="text-[var(--text-muted)] p-8 text-center">
                {t("common.no_results")}
              </p>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {signals.map((signal) => (
                <div
                  key={signal.id}
                  className="rounded-lg border p-4 bg-[var(--bg-primary)] space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-sm">{signal.name}</h3>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">
                        {signal.ar_name}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-xs font-medium",
                        severityColor(signal.severity),
                      )}
                    >
                      {signal.severity}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--text-secondary)] line-clamp-2">
                    {signal.description}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-[var(--text-disabled)]">
                    <span>{signal.domain}</span>
                    <span>{signal.source}</span>
                    <span className="font-medium">
                      {signal.weight.toFixed(2)}
                    </span>
                  </div>
                  <button
                    onClick={() => handleSubscribe(signal.id)}
                    disabled={subscribing === signal.id}
                    className="w-full rounded-lg bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] px-3 py-2 text-sm font-medium hover:bg-[var(--muhide-orange)]/20 transition disabled:opacity-50"
                  >
                    {subscribing === signal.id
                      ? t("common.loading")
                      : t("signals.subscribe")}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </TabsPanel>

        <TabsPanel value="feed">
          <div className="space-y-3">
            {feed.length === 0 && (
              <p className="text-[var(--text-muted)] p-8 text-center">
                {t("common.no_results")}
              </p>
            )}
            {feed.map((event) => (
              <div
                key={event.id}
                className={cn(
                  "rounded-lg border p-4 bg-[var(--bg-primary)]",
                  !event.acknowledged &&
                    "border-l-4 border-l-[var(--muhide-orange)]",
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono text-[var(--text-disabled)]">
                      {event.signal_id}
                    </span>
                    <span className="text-xs text-[var(--text-disabled)] mx-2">
                      |
                    </span>
                    <span className="text-xs text-[var(--text-disabled)]">
                      {event.company_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[var(--text-disabled)]">
                      {new Date(event.detected_at).toLocaleString("ar-SA")}
                    </span>
                    {!event.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(event.id)}
                        className="text-xs px-2 py-1 rounded bg-[var(--status-success-bg)] text-[var(--status-success-text)] hover:brightness-95"
                      >
                        {t("signals.acknowledge")}
                      </button>
                    )}
                    {event.acknowledged && (
                      <span className="text-xs text-[var(--text-disabled)] flex items-center gap-1">
                        <CheckCheck className="h-3 w-3" />{" "}
                        {t("signals.acknowledged")}
                      </span>
                    )}
                  </div>
                </div>
                {Object.keys(event.data).length > 0 && (
                  <pre className="mt-2 text-xs text-[var(--text-muted)] bg-[var(--bg-secondary)] p-2 rounded overflow-x-auto">
                    {JSON.stringify(event.data, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </TabsPanel>

        <TabsPanel value="subscriptions">
          <div className="space-y-3">
            {subscriptions.length === 0 && (
              <p className="text-[var(--text-muted)] p-8 text-center">
                {t("signals.no_subscriptions")}
              </p>
            )}
            {subscriptions.map((sub) => (
              <div
                key={sub.id}
                className="rounded-lg border p-4 bg-[var(--bg-primary)] flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-medium">{sub.signal_id}</p>
                  <p className="text-xs text-[var(--text-disabled)]">
                    {t("signals.channel")}: {sub.channel}
                    <span className="mx-2">|</span>
                    {t("company")}: {sub.company_id}
                  </p>
                </div>
                <button
                  onClick={() => handleUnsubscribe(sub.id)}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-[var(--status-danger-bg)] text-[var(--status-danger-text)] hover:brightness-95"
                >
                  <BellOff className="h-3 w-3" />
                  {t("signals.unsubscribe")}
                </button>
              </div>
            ))}
          </div>
        </TabsPanel>
      </Tabs>
    </div>
  );
}
