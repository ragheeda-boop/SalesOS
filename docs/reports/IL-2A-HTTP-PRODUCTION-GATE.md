# IL-2A — HTTP Production Gate (2026-08-12)

**Status:** **PASS** (HTTP evaluate → `decision.created` → AgentTask)  
**Validation label:** **light validated** (live prod)  
**Deploy SHA (gate):** `9304265a68e169acd7c3bfb7a2df0b94d98c2cca`  
**Scope:** Railway production · no `feature_ai_copilot` flip · no alembic upgrade

## Gate evidence

| Check | Result |
|-------|--------|
| HTTP `POST …/decision/evaluate` | **200** ~19ms |
| Decision | `5e05adbd-9b59-4d47-b80f-1818a7c27c21` (`recommend_call`) |
| AgentTask | `5be70b3e-7deb-45a6-8781-940b3149041b` (`research_company`, **COMPLETED**) |
| `domain_events.decision.created` | persisted |

## Hang-fix SHAs (prerequisite)

| SHA | Fix |
|-----|-----|
| `69c6e835` | JSONB bind via `CAST` + dumps (`_save_decision`) |
| `c5af184` / `de07be3` | Non-blocking `decision.created` publish; flush evaluate JSON before audit/fan-out |
| `9304265` | Fail-open event store → still fan-out in-process; bound store pool use |
| `4f52f68` | Bound timeline/IL-2A retries + subscriber timeouts |

Related probes: [`IL-2A-SAVE-DECISION-DB-PROBE.md`](./IL-2A-SAVE-DECISION-DB-PROBE.md), [`IL-2A-EVALUATE-HTTP-HANG-PROBE.md`](./IL-2A-EVALUATE-HTTP-HANG-PROBE.md).

## Residual (not a gate fail) — closed in follow-up

On a company that already had a `research_company` task (COMPLETED), re-evaluate hit `UniqueViolation` on `idempotency_key`, then logging used reserved LogRecord key `created` → **`KeyError: 'created'`**.

**Fix:** idempotency-key pre-check + IntegrityError savepoint fallback in `schedule_task`; triggers treat finished/UniqueViolation as **skipped**; log field renamed to `tasks_created` — commit `6a069d23`.

## Next (do not start without approval)

1. Residual **hardening** on claim/lease (beyond IL-2B.2 gate PASS) — not live ResearchAgent/LLM.
2. Staging parity / soak evidence (PRODUCTION_PLAN Wave 11 / STAR A-09).
3. Observability SLOs for evaluate + AgentTask fan-out (Wave 8) — **hooks landed** (`salesos_decision_evaluate_*`, `salesos_event_fanout_failures_total`, `salesos_agent_dispatch_errors_total` + alert rules); live Prometheus scrape / Alertmanager fire still **needs verify**.
4. Human secret rotations — [`HUMAN-SECRET-ROTATION-CHECKLIST.md`](./HUMAN-SECRET-ROTATION-CHECKLIST.md).

Program snapshot: [`PROGRAM-STATUS-2026-08-12.md`](./PROGRAM-STATUS-2026-08-12.md) (GA still **NO-GO**).

**Not started here:** ResearchAgent live LLM path, `feature_ai_copilot=True`.
