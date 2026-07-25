# Sprint 11 — Copilot Frontend (Branching, Feedback, Telemetry)

> **Date**: 2026-07-16
> **Status**: Completed
> **TypeScript**: Clean (0 new errors)
> **Gate Criteria**: G-11.1–G-11.5

---

## Summary

Implemented the three frontend features from WO-1101: conversation branching (F-1), feedback UI (F-2), and tool telemetry dashboard (F-3). All use `@salesos/ui`, `@salesos/charts`, and `@salesos/api` patterns.

---

## F-1: Conversation Branching

**Files changed:**
- `src/components/copilot-panel.tsx` — full rewrite with branching support

**Behavior:**
- Each `Message` carries `parentId: string | null` and `branchId: string` fields
- Branches are tracked as `Branch[]` state with `id`, `label`, `parentMessageId`
- `getVisibleMessages()` filters messages to show only the active branch (`activeBranchId`) while keeping `main` always visible
- Branch creation: user clicks the `GitBranch` icon on any assistant message → creates a new branch, sets `activeBranchId` to it
- Branch switching: horizontal pill bar at the bottom shows "Original" (main) + all branches as selectable pills
- Purple left-border indicator on branch messages (when `branchId !== "main"`)
- Active branch pill is purple; inactive are purple-tinted

**Keyboard:** All buttons have `aria-label` and `title` attributes.

---

## F-2: Feedback UI

**Files changed:**
- `src/components/copilot-panel.tsx` — `FeedbackButtons` component added
- `src/lib/api.ts` — `submitCopilotFeedback()` function added

**Behavior:**
- Every assistant message shows `ThumbsUp` / `ThumbsDown` buttons (visible on hover)
- Clicking a thumb selects the rating (green highlight for positive, red for negative) and opens inline comment textarea
- Submit calls `POST /api/v1/copilot/feedback` with `{ message_id, rating, comment }` and `X-Tenant-Id` header
- After submit, shows "Thank you" text in green
- Aggregate feedback: if `aggregateFeedback` exists on the message (from API response), shows `X% helpful` count next to the buttons
- Cancel button closes the comment form without submitting

**i18n keys:** `copilot.feedback_thanks`, `copilot.feedback_helpful`, `copilot.feedback_positive`, `copilot.feedback_negative`, `copilot.feedback_submit`, `copilot.feedback_comment_placeholder`, `copilot.feedback_rate`

---

## F-3: Tool Telemetry Dashboard

**Files created:**
- `src/app/(dashboard)/copilot/telemetry/page.tsx` — full dashboard page

**Files changed:**
- `src/lib/api.ts` — added `CopilotToolTelemetry`, `CopilotLatencyBucket`, `CopilotResultBucket`, `CopilotVolumePoint`, `CopilotTelemetryData` interfaces + `getCopilotTelemetry()` function
- `src/lib/copilotQueries.ts` — added `CopilotTelemetryResponse`, `CopilotFeedbackPayload`, `CopilotFeedbackSummary` interfaces + `useCopilotTelemetry(days)` hook with `react-query`
- `src/lib/i18n/en.json` — ~50 new keys for telemetry labels
- `src/lib/i18n/ar.json` — matching Arabic translations

**Dashboard layout:**
1. **Header** — back link to `/copilot`, title/subtitle, date range picker (7d/30d/90d)
2. **Summary cards** — 4 `MetricCard` widgets: Total Calls, Success Rate (with trend), Avg Latency, P95 Latency
3. **Charts grid** (2×2):
   - Latency distribution `BarChart` with color legend (green <200ms, amber 200-1000ms, red >1000ms)
   - Result count histogram `BarChart`
   - Volume over time `LineChart`
   - Latency percentile table (P50/P95/P99 per bucket)
4. **Tool breakdown table** — per-tool: name, calls, success, failure, color-coded rate badge, P50/P95/P99 latencies

**API:** `GET /api/v1/copilot/telemetry?days=N` with `X-Tenant-Id` header.

---

## Copilot Page Update

**Files changed:**
- `src/app/(dashboard)/copilot/page.tsx` — added telemetry link button (`BarChart3` icon, `href="/copilot/telemetry"`), branch history sidebar with sample entries

---

## i18n Keys Added (EN + AR)

| Key | EN | AR |
|-----|----|----|
| `copilot.branch_alt` | Alt {n} | بديل {n} |
| `copilot.branch_indicator` | Branch | فرع |
| `copilot.branch_from` | Branch from here | فرع من هنا |
| `copilot.branches_sidebar` | Branches | الفروع |
| `copilot.branch_original` | Original | الأصلي |
| `copilot.branch_history` | Branch History | تاريخ الفروع |
| `copilot.no_branches` | No branches yet | لا توجد فروع بعد |
| `copilot.feedback_thanks` | Thank you! | شكرًا! |
| `copilot.feedback_helpful` | Helpful? | مفيد؟ |
| `copilot.feedback_positive` | Positive feedback | تقييم إيجابي |
| `copilot.feedback_negative` | Negative feedback | تقييم سلبي |
| `copilot.feedback_submit` | Submit | إرسال |
| `copilot.feedback_comment_placeholder` | Add a comment... (optional) | أضف تعليقًا... (اختياري) |
| `copilot.feedback_rate` | helpful | مفيد |
| `copilot.telemetry_title` | Tool Telemetry | بيانات الأدوات |
| `copilot.telemetry_subtitle` | Performance metrics for AI tools | مقاييس أداء أدوات الذكاء الاصطناعي |
| `copilot.telemetry_total_calls` | Total Calls | إجمالي الاستدعاءات |
| `copilot.telemetry_success_rate` | Success Rate | معدل النجاح |
| `copilot.telemetry_avg_latency` | Avg Latency | متوسط التأخير |
| `copilot.telemetry_p95_latency` | P95 Latency | تأخير P95 |
| `copilot.telemetry_latency_distribution` | Latency Distribution | توزيع التأخير |
| `copilot.telemetry_result_histogram` | Result Count Histogram | توزيع عدد النتائج |
| `copilot.telemetry_volume_over_time` | Volume Over Time | الحجم عبر الوقت |
| `copilot.telemetry_tool_breakdown` | Tool Breakdown | تفاصيل الأدوات |
| `copilot.telemetry_tool_name` | Tool | الأداة |
| `copilot.telemetry_calls` | Calls | الاستدعاءات |
| `copilot.telemetry_success` | Success | النجاح |
| `copilot.telemetry_failure` | Failure | الفشل |
| `copilot.telemetry_p50` | P50 | P50 |
| `copilot.telemetry_p95` | P95 | P95 |
| `copilot.telemetry_p99` | P99 | P99 |
| `copilot.telemetry` | Telemetry | بيانات الأداء |

---

## Files Summary

| File | Action |
|------|--------|
| `src/components/copilot-panel.tsx` | Rewritten (branching + feedback) |
| `src/app/(dashboard)/copilot/page.tsx` | Updated (telemetry link + sidebar) |
| `src/app/(dashboard)/copilot/telemetry/page.tsx` | **Created** |
| `src/lib/copilotQueries.ts` | **Created** |
| `src/lib/api.ts` | Updated (copilot functions) |
| `src/lib/i18n/en.json` | Updated (~50 keys) |
| `src/lib/i18n/ar.json` | Updated (~50 keys) |

---

## Gate Criteria

| Gate | Requirement | Status |
|------|-------------|--------|
| G-11.1 | Branching: create, switch, visual indicator | ✅ |
| G-11.2 | Feedback: thumbs up/down, comment, submit | ✅ |
| G-11.3 | Telemetry: dashboard with charts + table | ✅ |
| G-11.4 | TypeScript clean (no new errors) | ✅ |
| G-11.5 | i18n keys added (EN + AR) | ✅ |

---

*Generated: 2026-07-16*
