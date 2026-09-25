"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LoadingState, EmptyState, ErrorState } from "../../_components/states";

interface EvidenceItem {
  id: string;
  company_name: string;
  evidence_type: string;
  channel: string;
  source_url: string;
  title: string;
  summary: string;
  confidence: number;
  collected_at: string;
}

interface Signal {
  id: string;
  company_name: string;
  signal_type: string;
  confidence: string;
  title: string;
  description: string;
  source_urls: string[];
  detected_at: string;
}

interface IntelSummary {
  company: string;
  evidence_count: number;
  signal_count: number;
  channels_searched: string[];
  last_researched: string | null;
  evidence: EvidenceItem[];
  signals: Signal[];
}

const CHANNEL_ICONS: Record<string, string> = {
  web: "🌐",
  github: "💻",
  linkedin: "🔗",
  twitter: "𝕏",
  youtube: "📺",
};

const SIGNAL_COLORS: Record<string, string> = {
  hiring: "text-emerald-600",
  funding: "text-blue-600",
  partnership: "text-purple-600",
  expansion: "text-amber-600",
  layoffs: "text-red-600",
  leadership: "text-indigo-600",
  product: "text-cyan-600",
  other: "text-[var(--text-muted)]",
};

function getAccessToken(): string {
  if (typeof window === "undefined") return "";
  try {
    const raw = localStorage.getItem("sb-localhost-auth-token");
    if (!raw) return "";
    return JSON.parse(raw)?.access_token ?? "";
  } catch {
    return "";
  }
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
  const [open, setOpen] = useState(false);
  const icon = CHANNEL_ICONS[item.channel] || "📡";
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span className="text-sm font-medium text-[var(--text-primary)]">
            {item.title || item.evidence_type}
          </span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {item.evidence_type}
          </span>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          {open ? "collapse" : "expand"}
        </button>
      </div>
      {item.summary && (
        <p className="mt-1 text-xs text-[var(--text-secondary)] line-clamp-2">
          {item.summary.slice(0, 200)}
        </p>
      )}
      {open && item.source_url && (
        <a
          href={item.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-[10px] text-[var(--accent-primary)] hover:underline"
        >
          View source →
        </a>
      )}
    </div>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const color = SIGNAL_COLORS[signal.signal_type] || "text-[var(--text-muted)]";
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
      <div className="flex items-center gap-2">
        <span className={`text-xs font-medium uppercase ${color}`}>
          {signal.signal_type}
        </span>
        <span
          className={`text-[10px] font-medium ${
            signal.confidence === "high"
              ? "text-emerald-600"
              : signal.confidence === "medium"
                ? "text-amber-600"
                : "text-[var(--text-muted)]"
          }`}
        >
          {signal.confidence}
        </span>
      </div>
      <p className="mt-1 text-sm text-[var(--text-primary)]">{signal.title}</p>
      {signal.source_urls.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {signal.source_urls.slice(0, 3).map((url, i) => (
            <a
              key={i}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-[var(--accent-primary)] hover:underline"
            >
              source {i + 1} →
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export function ExternalIntelTab({ companyName, companyId }: { companyName: string; companyId: string }) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"evidence" | "signals">("evidence");

  const { data: intel, isLoading: intelLoading } = useQuery({
    queryKey: ["agent-reach", "intel", companyId],
    queryFn: async (): Promise<IntelSummary> => {
      const token = getAccessToken();
      const res = await fetch(`/api/v1/agent-reach/intel/${encodeURIComponent(companyName)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) return { company: companyName, evidence_count: 0, signal_count: 0, channels_searched: [], last_researched: null, evidence: [], signals: [] };
      return res.json();
    },
  });

  const researchMutation = useMutation({
    mutationFn: async () => {
      const token = getAccessToken();
      const res = await fetch("/api/v1/agent-reach/research/company", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          company_name: companyName,
          channels: ["web", "github", "linkedin"],
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Research failed");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-reach", "intel", companyId] });
    },
  });

  const evidence = intel?.evidence || [];
  const signals = intel?.signals || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-[var(--text-primary)]">External Intelligence</h3>
          <p className="text-xs text-[var(--text-muted)]">
            Web research across GitHub, LinkedIn, and public sources
            {intel?.last_researched && (
              <> · Last: {new Date(intel.last_researched).toLocaleDateString()}</>
            )}
          </p>
        </div>
        <button
          onClick={() => researchMutation.mutate()}
          disabled={researchMutation.isPending}
          className="rounded-[var(--radius-md)] bg-[var(--accent-primary)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {researchMutation.isPending ? "Researching…" : "Run Research"}
        </button>
      </div>

      {researchMutation.isPending && <LoadingState label="Researching company across channels…" />}

      {researchMutation.isError && (
        <ErrorState
          title="Research failed"
          description={researchMutation.error instanceof Error ? researchMutation.error.message : undefined}
        />
      )}

      {intel && (
        <>
          <div className="flex gap-4 border-b border-[var(--border-default)] pb-2">
            <button
              onClick={() => setActiveTab("evidence")}
              className={`text-xs font-medium ${
                activeTab === "evidence"
                  ? "text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              Evidence ({evidence.length})
            </button>
            <button
              onClick={() => setActiveTab("signals")}
              className={`text-xs font-medium ${
                activeTab === "signals"
                  ? "text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              Signals ({signals.length})
            </button>
          </div>

          {activeTab === "evidence" && (
            <div className="space-y-2">
              {evidence.length === 0 ? (
                <EmptyState
                  title="No evidence yet"
                  description="Run research to gather external intelligence."
                />
              ) : (
                evidence.map((item) => <EvidenceCard key={item.id} item={item} />)
              )}
            </div>
          )}

          {activeTab === "signals" && (
            <div className="space-y-2">
              {signals.length === 0 ? (
                <EmptyState
                  title="No signals detected"
                  description="Signals are auto-extracted from evidence. Run research first."
                />
              ) : (
                signals.map((s) => <SignalCard key={s.id} signal={s} />)
              )}
            </div>
          )}
        </>
      )}

      {!intel && !intelLoading && (
        <EmptyState
          title="No external intelligence yet"
          description="Click Run Research to gather web intelligence for this company."
        />
      )}
    </div>
  );
}
