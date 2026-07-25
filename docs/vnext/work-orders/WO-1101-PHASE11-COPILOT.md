# Work Order WO-1101 — Phase 11: Copilot

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 ✅, Phase 9 ✅, Phase 10 ✅
> **Priority**: P0

---

## Scope

Copilot polish: fix search tool, feedback, telemetry, Arabic support, conversation branching.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Fix search_companies tool** — ensure it returns populated results with < 1s latency | 1d |
| B-2 | **Copilot feedback** — `POST /copilot/feedback` (thumbs up/down + comment), link to conversation | 1d |
| B-3 | **Tool telemetry** — log tool calls: tool_name, success/fail, latency_ms, result_count, timestamp | 1.5d |
| B-4 | **Arabic copilot** — Arabic NLP pipeline, RTL text handling, Saudi business context prompts | 1.5d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Conversation branching** — branch point UI, explore alternatives without losing context | 2d |
| F-2 | **Feedback UI** — thumbs up/down on copilot responses + comment | 1d |
| F-3 | **Tool telemetry dashboard** — success rate, latency, result distribution | 1.5d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-11.1 | search_companies returns results < 1s |
| G-11.2 | Feedback submission rate > 10% target |
| G-11.3 | Tool telemetry: success rate, p50/p95/p99 latency |
| G-11.4 | Arabic copilot: RTL, Arabic questions, Saudi context |
| G-11.5 | Branch points for exploring alternatives |

---

**Engineering OS**: ✅ Approved
