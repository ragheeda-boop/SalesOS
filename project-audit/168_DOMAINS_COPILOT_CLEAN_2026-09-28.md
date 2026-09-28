# 168 — `domains/copilot` fully clean (properly tenant-scoped, honestly disclosed as ephemeral); two cosmetic text-corruption artifacts confirmed to have zero behavioral impact, documented not fixed

**Read-only.** No files changed. No database or container needed — the two cosmetic findings below were confirmed to have zero observable effect via direct interpreter testing, not assumption.

## 1. Scope

Continuing the `domains/` sweep: `domains/copilot` (981 lines: `models.py`, `feedback_service.py`, `telemetry_service.py`, `schemas.py`, `tools.py`, `arabic.py`), and its live consumer `app/routers/copilot.py`.

## 2. `CopilotFeedbackService` / `ToolTelemetryService` — fully clean, correctly tenant-scoped

Both are explicitly, honestly disclosed as temporary (`"In-memory store for feedback records... Will be swapped for PostgreSQL repository in production"`) — unlike report 167's `domains/ai` finding, this is not a silent gap. Critically, unlike that finding, `CopilotFeedback`/`ToolCallRecord` **do** carry a `tenant_id` field, and every read method (`get_stats`/`list_feedback`/`count`/`get_tool_breakdown`/`get_volume_over_time`) correctly filters by it whenever supplied. Confirmed every real call site in `app/routers/copilot.py` (`submit_feedback`/`feedback_stats`/`telemetry_dashboard`/etc.) passes the **real, authenticated** `tenant_id` from `Depends(get_current_tenant_id)`, not a client-supplied value — this domain does not share `domains/ai`'s cross-tenant leak.

One harmless dead-code redundancy noted, not fixed: `ToolTelemetryService.get_volume_over_time()` computes `bucket_key` at line 152 and immediately overwrites it with a differently-formatted value at line 154 — the first computation's result is never used. Purely cosmetic; the final bucketing logic is correct.

## 3. `ArabicCopilotEngine` — two text-corruption artifacts, confirmed zero behavioral impact

Found two garbled-text artifacts, both consistent with a lossy copy-paste/encoding mishap rather than deliberate design:

- `_CR_PATTERN`'s regex alternation includes `سجل\s*ال thương` — Vietnamese text ("thương") embedded mid-pattern where correct Arabic text should be. Confirmed directly (imported the real compiled pattern, not a re-transcription): the regex still compiles correctly and `detect()` still correctly flags `commercial_registration` for real English (`"CR: ..."`) and Arabic (`"سجل تجاري: ..."`) input, via the pattern's *other* valid alternatives. The garbled alternative simply never matches anything and is inert.
- `SAUDI_CONTEXT_TERMS`'s dict has a key `"منصة_ embod"` (garbled) where the paired value ("Qiwa — Saudi Labor Platform") implies the intended key was the Arabic name for the Qiwa platform. Confirmed via a repo-wide grep that this dict is only ever iterated (`len(...)`) or checked for a *different*, uncorrupted key (`"سجل_تجاري"`) in its one existing test — nothing anywhere looks up this specific key, so the corruption currently changes no observable behavior.

**Not fixed**: per this session's established discipline, "fixed" is reserved for genuine, reproducible defects with a real red→green cycle. Manufacturing a test to prove a behavioral difference here would be dishonest, since none exists today — both artifacts are dead weight, not live bugs. Documented for a future, low-priority hygiene pass (correcting the garbled text is safe and unambiguous whenever someone next touches this file) rather than claimed as a fix in this report.

## 4. Scope and safety

- No files changed. No database or container needed.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining `domains/` candidate: `domains/rag` (`domains/ubom` deferred, explicitly marked DEPRECATED). This closes the planned `domains/` sweep from reports 155-168 after `domains/rag` is checked.
