"use client";

import { useState } from "react";
import { X, CheckCircle2, XCircle, AlertTriangle, Brain, ThumbsUp, ArrowRight, Shield } from "lucide-react";

const TRUST_RULES = [
  {
    icon: Brain,
    label: "Trust AI when...",
    color: "text-green-600",
    bg: "bg-[var(--bg-secondary)]",
    rules: [
      "Signal has high confidence (0.8+) and 3+ evidence sources",
      "Intent score is 85+ with CRM boost applied",
      "Recommendation aligns with your account knowledge",
      "Multiple data sources corroborate the same insight",
      "You have no contradictory information from direct contact",
    ],
  },
  {
    icon: Shield,
    label: "Override AI when...",
    color: "text-orange-600",
    bg: "bg-[var(--bg-secondary)]",
    rules: [
      "You have direct knowledge the AI lacks (recent call, email thread)",
      "The company changed strategy or budget since signal was detected",
      "A competitor relationship exists the AI cannot see",
      "The recommended action conflicts with your territory/account plan",
      "Timing is wrong (budget cycle, internal initiative, PTO)",
    ],
  },
  {
    icon: AlertTriangle,
    label: "Escalate to your manager when...",
    color: "text-red-600",
    bg: "bg-[var(--bg-secondary)]",
    rules: [
      "AI recommends a high-value action but you disagree on approach",
      "Signal suggests opportunity but your gut says risk",
      "Conflicting signals from different sources on the same account",
      "You are unsure whether to accept or reject a recommendation",
    ],
  },
];

const OVERRIDE_REASONS = [
  { code: "wrong_person", label: "Wrong Person", desc: "Recommendation targets incorrect contact" },
  { code: "bad_timing", label: "Bad Timing", desc: "Action is premature or poorly timed" },
  { code: "not_relevant", label: "Not Relevant", desc: "Signal does not apply to this account" },
  { code: "already_contacted", label: "Already Contacted", desc: "This touchpoint was already executed" },
  { code: "budget_constraint", label: "Budget Constraint", desc: "Account has no budget for this action" },
];

export default function SellerGuidance({ onClose }: { onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<"trust" | "override" | "feedback">("trust");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)]">
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Seller Operating Model</h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">How to work with AI recommendations</p>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[var(--border-primary)]">
          {[
            { key: "trust" as const, label: "Trust vs Override" },
            { key: "override" as const, label: "Override Reasons" },
            { key: "feedback" as const, label: "Feedback Loop" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "text-[var(--text-primary)] border-b-2 border-[var(--text-primary)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-5 overflow-y-auto max-h-[60vh]">
          {activeTab === "trust" && (
            <div className="space-y-5">
              {TRUST_RULES.map((section) => (
                <div key={section.label} className="rounded-lg border border-[var(--border-primary)] p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <section.icon className={`w-4 h-4 ${section.color}`} />
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">{section.label}</h3>
                  </div>
                  <ul className="space-y-2">
                    {section.rules.map((rule, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-muted)]">
                        <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-[var(--text-muted)]" />
                        {rule}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          {activeTab === "override" && (
            <div className="space-y-3">
              <p className="text-sm text-[var(--text-muted)] mb-4">
                When rejecting a recommendation, select the reason that best explains your override.
                This feedback directly improves future recommendations for your accounts.
              </p>
              {OVERRIDE_REASONS.map((reason) => (
                <div key={reason.code} className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border-primary)]">
                  <XCircle className="w-4 h-4 text-[var(--text-muted)] mt-0.5 shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-[var(--text-primary)]">{reason.label}</div>
                    <div className="text-xs text-[var(--text-muted)] mt-0.5">{reason.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "feedback" && (
            <div className="space-y-4">
              <div className="rounded-lg border border-[var(--border-primary)] p-4">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">How your feedback improves recommendations</h3>
                <div className="space-y-3 text-xs text-[var(--text-muted)]">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3 h-3 mt-0.5 shrink-0 text-[var(--text-primary)]" />
                    <span><strong>Accept</strong> reinforces the signal pattern. Similar accounts will see the same recommendation with higher priority.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <XCircle className="w-3 h-3 mt-0.5 shrink-0 text-[var(--text-secondary)]" />
                    <span><strong>Reject</strong> teaches the system what does not work for your accounts. The pattern will be deprioritized for similar signals.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ThumbsUp className="w-3 h-3 mt-0.5 shrink-0 text-[var(--text-muted)]" />
                    <span><strong>Modify</strong> captures your judgment about the right approach. The system learns your preferred action types and timing.</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border-primary)] p-4">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Outcome tracking</h3>
                <div className="text-xs text-[var(--text-muted)] space-y-2">
                  <p>After taking an action, log the outcome (connected, meeting set, no answer, etc.). This closes the feedback loop:</p>
                  <ol className="list-decimal list-inside space-y-1 ml-2">
                    <li>Signal detected and recommendation generated</li>
                    <li>You accept or override the recommendation</li>
                    <li>You execute the action (call, email, meeting)</li>
                    <li>You log the outcome</li>
                    <li>If positive, a follow-up is auto-generated</li>
                    <li>Your acceptance rate and conversion metrics update</li>
                  </ol>
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border-primary)] p-4">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Key metrics to watch</h3>
                <div className="grid grid-cols-2 gap-3 text-xs text-[var(--text-muted)]">
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">Acceptance Rate</div>
                    <div>How often you follow AI recommendations. Higher is not always better -- override when you have better information.</div>
                  </div>
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">Conversion Rate</div>
                    <div>Percentage of actions that result in a positive outcome (connected, meeting set, proposal sent).</div>
                  </div>
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">Time-to-Action</div>
                    <div>Average hours between recommendation and your first response. Faster response correlates with higher conversion.</div>
                  </div>
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">Follow-up Rate</div>
                    <div>Outcomes that generate follow-ups. A high rate means you are building pipeline, not just making calls.</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
