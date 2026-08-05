"use client";

import {
  useEmailKPIs,
  useEmailTopContacts,
  useEmailDailyVolume,
} from "@/lib/hooks/employeeQueries";
import { Card, CardContent, CardHeader, Skeleton } from "@salesos/ui";
import { Mail, Send, Inbox, Clock, Smile, Frown, BarChart3 } from "lucide-react";

export function EmailDashboard({ employeeId }: { employeeId: string }) {
  const { data: kpis, isLoading } = useEmailKPIs(employeeId);
  const { data: topContacts } = useEmailTopContacts(employeeId);
  const { data: dailyVolume } = useEmailDailyVolume(employeeId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <EmailKPI
          label="Sent"
          value={kpis.sent}
          icon={Send}
          color="bg-blue-50 dark:bg-blue-900/20"
        />
        <EmailKPI
          label="Received"
          value={kpis.received}
          icon={Inbox}
          color="bg-purple-50 dark:bg-purple-900/20"
        />
        <EmailKPI
          label="Reply Rate"
          value={`${kpis.reply_rate}%`}
          icon={Mail}
          color="bg-green-50 dark:bg-green-900/20"
        />
        <EmailKPI
          label="Avg Response"
          value={`${kpis.avg_response_hours}h`}
          icon={Clock}
          color="bg-amber-50 dark:bg-amber-900/20"
        />
        <EmailKPI
          label="Unread"
          value={kpis.unread_count}
          icon={Mail}
          color="bg-red-50 dark:bg-red-900/20"
        />
        <EmailKPI
          label="Internal"
          value={kpis.internal}
          icon={Inbox}
          color="bg-slate-50 dark:bg-slate-900/20"
        />
        <EmailKPI
          label="External"
          value={kpis.external}
          icon={Send}
          color="bg-orange-50 dark:bg-orange-900/20"
        />
        <EmailKPI
          label="With Files"
          value={kpis.has_attachments}
          icon={BarChart3}
          color="bg-teal-50 dark:bg-teal-900/20"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {topContacts && topContacts.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-sm font-semibold">Top Contacts</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {topContacts.slice(0, 10).map((c, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-[var(--text-secondary)] truncate max-w-[200px]">
                      {c.address}
                    </span>
                    <span className="font-medium">{c.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {dailyVolume && dailyVolume.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-sm font-semibold">Daily Volume</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {dailyVolume.slice(-14).map((d, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-20 text-[var(--text-muted)]">{d.date?.slice(5)}</span>
                    <div className="flex-1 h-3 flex rounded-full overflow-hidden bg-[var(--bg-tertiary)]">
                      <div
                        className="h-full bg-blue-400"
                        style={{
                          width: `${Math.min(100, (d.sent / Math.max(1, d.sent + d.received)) * 100)}%`,
                        }}
                      />
                      <div
                        className="h-full bg-green-400"
                        style={{
                          width: `${Math.min(100, (d.received / Math.max(1, d.sent + d.received)) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="w-12 text-right">{d.sent + d.received}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="flex gap-3 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-blue-400" /> Sent: {kpis.sent}
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-green-400" /> Received: {kpis.received}
        </div>
        <div className="flex items-center gap-1">
          <Smile className="h-3 w-3 text-green-500" /> Positive: {kpis.sentiment_positive}
        </div>
        <div className="flex items-center gap-1">
          <Frown className="h-3 w-3 text-red-500" /> Negative: {kpis.sentiment_negative}
        </div>
      </div>
    </div>
  );
}

function EmailKPI({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className={`rounded-xl border p-4 ${color}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">{label}</span>
        <Icon className="h-4 w-4 opacity-50" />
      </div>
      <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}
