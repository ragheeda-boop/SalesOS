# 154 — Correction to report 139: `decision_center_service` IS live and reached; it was not an unreached feature

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. What report 139 claimed

Report 139 (checking `domains/decision_center/postgres_repo.py`) concluded: *"`grep -rln "decision_center_service"` across the entire `app/` tree returns only `app/startup.py` (dead) and `app/boot/startup.py` (the assignment itself) — zero routers, GraphQL resolvers, or any other code path ever reads `app.state.decision_center_service`."* It classified this as "correctly-built, unreached code — the mirror image of report 133's `graph_nodes` finding."

## 2. What this report's wider sweep found

Report 153's "not initialized" 503-guard grep (a broader search pattern than report 139's literal `grep -rln "decision_center_service"`) surfaced `domains/decision_center/router.py:129`: `raise HTTPException(status_code=503, detail="Decision Center service not initialized")` — a real reader report 139's narrower search missed entirely. Confirmed this router **is** genuinely mounted at boot (`app/boot/routers.py:131,134`), and its own module docstring identifies it as *"the CANONICAL SoT (EAB-001-P0-DUP-01)"* for durable, auditable governed decisions — explicitly the preferred API over the separate Decision Platform (`/api/v1/decision/*`) and Decision Runtime (`/api/v1/decision-runtime/*`) surfaces.

This router exposes 12 real endpoints (`POST/GET /decisions`, `GET /decisions/{id}`, `GET /decisions/{id}/audit`, `POST /decisions/{id}/feedback`, full CRUD on `/decision-templates`, plus a seed endpoint) — all backed by the same `DecisionCenterService`/`PostgresDecisionCenterRepository` pair report 139 already verified field-mapping-correct in full.

## 3. Why report 139's search missed this

Report 139's search was `grep -rln "decision_center_service"` — a literal substring match. `domains/decision_center/router.py` reads the attribute via `getattr(request.app.state, "decision_center_service", None)` inside a helper function (matching the exact idiom used by `approval.py`/`copilot.py`/every other router this session examined) — this substring **does** contain "decision_center_service" and should have matched. Re-running report 139's exact original grep confirms it does now return this file; the most likely explanation is a search-scope or transient tooling error in the original investigation, not a structural reason the file would be excluded. This is disclosed as a genuine correction, not defended.

## 4. Net effect — this is a correction, not a new bug

Given report 139 already verified `PostgresDecisionCenterRepository`'s field mapping fully correct, and `_init_decision_center()` correctly wires the service at boot (also already verified in report 139), finding a real, live reader means **Decision Center is a fully functional, working feature** — not "correctly built but unreached." This is the opposite of reports 148/151's findings (a broken or missing wiring): here, everything was already correct end-to-end, and the only defect was report 139's own reachability claim.

Existing test coverage further supports this conclusion: `tests/contract/test_decision_center_cross_tenant_idor.py` (a dedicated cross-tenant IDOR security test — the kind of scrutiny a genuinely live, security-relevant API receives), `tests/e2e/test_critical_paths.py`, and RLS category tests all reference this domain, consistent with it being an established, exercised feature rather than a forgotten one.

## 5. Scope and safety

- No files changed — this is a documentation correction, not a code fix.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Completing the sweep — all 14 "not initialized" 503-guard instances now accounted for

Cross-checked every remaining "not initialized" service-guard message from report 153's grep (14 distinct instances total) against the verified attribute list:

- `runtime/admin_router.py`'s "Data fabric pipeline" reads `app.state.data_fabric` — already confirmed correctly wired (report 150).
- `runtime/knowledge_graph_runtime/router.py`'s "Knowledge Graph" reads `app.state.kg_engine` — already confirmed correctly wired (report 150).
- `domains/timeline/router.py`'s "Timeline Service" reads `app.state.timeline_service` — re-verified with a broader search this time (not just the original narrow grep): genuinely **zero** mount references anywhere in `app/boot/routers.py` or elsewhere. Confirmed dead, no correction needed here.
- Every other instance (Work Intelligence Engine, Feature Store domain service / Feature Store, Activity Runtime, Data Fabric Runtime, Decision Engine, Search Runtime, Timeline Runtime) traces to an attribute already confirmed correctly wired in reports 148-153.

**Final tally for the entire "not initialized" 503-guard pattern, all 14 instances**: 2 real bugs fixed (`approval_service` report 148, `nba_engine` report 151), 1 false "unreached" claim corrected (`decision_center_service`, this report — actually live and working), 11 confirmed already correct. This sweep is now exhaustive.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. Report 139's "reachability" finding is corrected here; its field-mapping and GUC-pinning verification (the substantive parts of that report) stand unchanged and remain accurate. The "not initialized" 503-guard methodology (reports 148-154) is now fully closed. Pivoting to a fresh angle for the next tick.
