# Operations Manual — Runbooks

> **Audience:** DevOps/SRE, Backend on-call, Support Console operators. Every runbook below must be **exercised at least once in a drill before GA** per `PRODUCTION_READINESS_CHECKLIST.md` §Documentation — a runbook that has only ever been read, never run, is not considered production-ready.
> **Format:** Trigger → Preconditions → Steps → Verification → Rollback → Escalation.

---

## 1. Deployment

**Trigger:** A merged PR reaches the deploy pipeline for staging or production.

**Preconditions:** CI green (unit, integration, contract, coverage gate); for production deploys, staging soak of ≥24 hours with no new P0/P1.

**Steps:**
1. Deploy to staging via the CI/CD pipeline's blue/green (or canary) mechanism.
2. Run the automated smoke-test suite against staging (subset of Playwright critical journeys).
3. If smoke tests pass, promote the same build artifact to production canary (5% of traffic, or 1 tenant cohort for pooled tier).
4. Monitor canary for 30 minutes against SLO dashboards (error rate, latency, entitlement-check failures).
5. If canary is clean, complete rollout to 100%.

**Verification:** Post-deploy dashboard shows error rate and latency within baseline for 30 minutes at 100% rollout; no new entries in the cross-tenant adversarial suite's continuous run.

**Rollback:** See §2.

**Escalation:** If canary shows any P0-severity signal, DevOps/SRE halts rollout immediately and pages Backend Lead — do not wait for the 30-minute window to complete.

---

## 2. Rollback

**Trigger:** A production deploy shows a P0/P1 regression (via canary monitoring, alert, or customer report).

**Preconditions:** The previous build artifact is available and was itself verified stable (never roll back to an unverified build).

**Steps:**
1. Determine rollback lever, in this preference order (per `RELEASE_PLAN.md` §GA rollback plan): (a) feature-flag-disable the specific broken capability if isolated, (b) roll forward with a hotfix if the fix is trivial and well-understood, (c) full build revert to the last-known-good artifact.
2. Execute the chosen lever via the CI/CD pipeline's single documented revert action.
3. Confirm the regression signal clears within 15 minutes of the rollback taking effect.
4. Notify affected tenants if the incident was customer-visible (per §3 Incident Response communication steps).

**Verification:** SLO dashboards return to baseline; the specific regression's reproduction steps no longer reproduce.

**Rollback of the rollback:** N/A by design — a rollback target is always a previously-verified-stable build, so there is no further fallback needed.

**Escalation:** Full build revert (option c) at the GA stage requires CTO + Release Manager joint sign-off per `RELEASE_PLAN.md`, given billing/customer-communication implications — page both immediately if this lever is being considered.

---

## 3. Incident Response

**Trigger:** A P0/P1 alert fires, or a customer reports a critical issue.

**Preconditions:** On-call rotation staffed (24/7 from GA per `PRODUCTION_READINESS_CHECKLIST.md` §Support).

**Steps:**
1. On-call engineer acknowledges the page within the SLA (target: 5 minutes for P0).
2. Assess severity: P0 (tenant-data-affecting or platform-wide outage), P1 (degraded but not down), P2 (isolated/cosmetic).
3. For P0: open a war room (dedicated incident channel), page Backend Lead + DevOps/SRE + Program Director.
4. Mitigate first (stop the bleeding — rollback, flag-disable, or scale-up), diagnose root cause second. Do not spend the first 15 minutes root-causing a live P0 instead of mitigating.
5. Once mitigated, communicate status to affected tenants via the Support Console (CAP-075) status mechanism.
6. Write a postmortem within 48 hours — blameless, root-cause-focused, with concrete action items and owners.

**Verification:** Incident is declared resolved only when the mitigating action is confirmed holding for at least 30 minutes post-mitigation, not at the moment the fix is deployed.

**Rollback:** See §2 if the mitigation itself was a deploy.

**Escalation:** Any P0 lasting beyond 1 hour without a clear mitigation path escalates to CTO directly, regardless of time of day.

---

## 4. Scaling

**Trigger:** Platform Health (CAP-074) shows sustained resource utilization above 70% on any tier, or a noisy-neighbor alert fires for a specific tenant.

**Preconditions:** Load-test baseline established (Phase 6) so "above baseline" has a concrete reference point.

**Steps:**
1. Identify whether the pressure is platform-wide (scale the pooled tier) or single-tenant (investigate noisy-neighbor — is this tenant exceeding their plan's quota, and if so, is quota enforcement (EPIC-06) actually engaging?).
2. For platform-wide pressure: scale the pooled Postgres cluster/application tier horizontally per the provisioned infrastructure's standard scaling procedure.
3. For a single noisy tenant: confirm `UsageMeter` is correctly tracking their consumption; if within quota but still causing platform pressure, this is a Phase 6 load-test assumption violation — escalate to Chief Architect, don't just add capacity silently (the assumption itself may need revisiting).

**Verification:** Utilization returns below 70% sustained; no SLO breach recorded during the scaling event.

**Rollback:** Scale back down once utilization is sustained below 40% for 24 hours (avoid flapping).

**Escalation:** If a single Enterprise tenant's legitimate (in-quota) usage repeatedly triggers platform-wide scaling events, this is a signal the siloed-tenant tier (deferred per A6) needs to pull forward — escalate to CPO/Chief Architect as a roadmap decision, not just an infra ticket.

---

## 5. Monitoring

**Trigger:** Continuous — this runbook describes what "healthy" looks like and how to read the dashboards, for onboarding new on-call engineers.

**Steps:**
1. Platform Health dashboard (CAP-074): uptime, latency, error budget, per-tenant resource consumption — the first place to look for any alert.
2. Connector sync dashboard: `SyncRun` status per connection — a red row means a tenant's data is stale, treat as P1 minimum.
3. Billing dashboard: subscription state distribution — a spike in `past_due` states may indicate a Stripe integration issue, not just customer payment problems.
4. AI cost dashboard: per-tenant token consumption against plan ceilings — a tenant consistently near their ceiling is a sales upsell signal, not just an ops concern.

**Verification:** All 4 dashboards load and reflect data no more than 5 minutes stale.

**Escalation:** A dashboard itself being stale/broken is treated as a P1 (you can't operate what you can't see).

---

## 6. Support

**Trigger:** A support ticket is filed (any tier).

**Steps:**
1. Triage against the tier's SLA (per `COMMERCIAL_LAUNCH_PLAN.md` §SLA) — P0/P1/P2 classification.
2. Use Support Console (CAP-075) for any tenant-specific investigation — impersonation requires explicit tenant consent and is time-boxed and fully audited (never standing access).
3. If the issue requires code investigation, file an engineering ticket cross-referenced to the support ticket ID.
4. Close the loop with the tenant, including a plain-language summary of root cause for P0/P1 tickets (not just "fixed").

**Verification:** SLA adherence tracked and reported monthly (`MASTER_EXECUTION_PLAN.md` §8 target: ≥95%).

**Escalation:** Any ticket touching billing/entitlement disputes escalates to Program Director, not resolved unilaterally by a support operator.

---

## 7. Database Maintenance

**Trigger:** Scheduled (weekly) + as-needed (e.g., before a major migration).

**Steps:**
1. Review slow-query log weekly; any query newly appearing above the 100ms p95 threshold (per `PRODUCTION_READINESS_CHECKLIST.md`) is ticketed.
2. Vacuum/analyze scheduling reviewed monthly against actual table growth (especially the monthly-partitioned high-volume tables).
3. Before any schema migration: verify Alembic head matches models, take a pre-migration backup snapshot, run the migration against a staging replica first.
4. Index health review monthly — confirm the mandatory `(tenant_id, updated_at)` composite indexes remain in place and are actually being used by the query planner (not just present).

**Verification:** No query regression introduced; migration applies cleanly to staging before touching production.

**Rollback:** Every migration ships with a documented down-migration, tested on staging before the up-migration ever reaches production.

---

## 8. Secrets Rotation

**Trigger:** Scheduled (quarterly) + as-needed (suspected compromise).

**Steps:**
1. Rotate AI provider API keys (`AIProviderRegistration`) — update in the secrets vault, verify the AI Provider Gateway picks up the new credential without a deploy (config reload, not code change).
2. Rotate the platform's own signing keys (JWT) with an overlap window (old + new both valid briefly) to avoid mass session invalidation.
3. Connector credentials (`ExternalSystemConnection.credential_ref`) are tenant-owned — rotation is tenant-initiated via Integrations Studio, not a platform-wide operation; this runbook covers only platform-level secrets.
4. Verify no secret appears in logs post-rotation (spot-check against the log-scrubbing audit).

**Verification:** All rotated secrets confirmed working via a synthetic transaction (e.g., a test AI call, a test JWT issuance) before declaring rotation complete.

**Escalation:** Suspected compromise triggers immediate rotation (skip the quarterly schedule) and a security incident review, regardless of confirmed impact.

---

## 9. AI Provider Failover

**Trigger:** Primary AI provider unavailable (timeout, 5xx, or explicit outage notification) for more than 30 seconds.

**Preconditions:** Secondary provider registered and pre-validated (per CAP-077 AI Provider Fleet Management), model-tier-equivalence mapping documented (which secondary model substitutes for which primary model per plan tier).

**Steps:**
1. AI Provider Gateway detects sustained failure (circuit breaker trips after N consecutive failures, N defined and tuned in Phase 6 chaos testing).
2. Traffic automatically routes to the secondary provider per the pre-defined mapping.
3. Alert fires to AI Lead + DevOps/SRE — failover is automatic, but human awareness is mandatory, not optional.
4. Once the primary provider's health check passes again for a sustained window (avoid flapping), traffic gradually shifts back.

**Verification:** Failover engages within 30 seconds (per `PRODUCTION_READINESS_CHECKLIST.md`); tenant-facing AI features degrade gracefully (e.g., a note about "using backup AI provider," not a hard failure) rather than becoming unavailable.

**Rollback:** N/A — failback to primary is itself the "rollback," handled automatically per step 4.

**Escalation:** If both primary and secondary providers are unavailable simultaneously, this is a P0 — AI features fail closed with a clear tenant-facing message, and CTO is paged.

---

## 10. Connector Failures

**Trigger:** A `SyncRun` fails, or the field-mapping drift-detection job fires.

**Steps:**
1. Check the specific failure mode: connection unreachable (network/auth issue), field-mapping drift (a mapped field disappeared/renamed at the source), or malformed data (a record fails Validator-stage checks in the Anti-Corruption Layer).
2. **Connection unreachable:** retry with exponential backoff (already built into the adapter per `PROGRAM_PLAN.md` EPIC-09); if retries exhaust, mark the connection `status=error`, alert the tenant via Integrations Studio's monitor view, do not silently keep retrying forever.
3. **Field-mapping drift:** the sync does not silently null the missing field — it halts that field's mapping specifically, alerts the tenant admin (who owns `FieldMappingConfig` for their tenant) to re-map, and continues syncing all other unaffected fields.
4. **Malformed data:** the specific record is quarantined (logged, not written to canonical tables), sync continues for all other valid records — one bad record must never halt an entire sync run.

**Verification:** `SyncRun` history shows the failure classified correctly (not a generic "failed" status) and the tenant-facing monitor view reflects the same classification.

**Rollback:** N/A — a failed sync simply doesn't write; there's no partial-write state to roll back given the transactional write pattern (per `SAAS_PLATFORM_ARCHITECTURE.md` §5, canonical writes are transactional with their Outbox entry).

**Escalation:** A connector down for more than 24 hours (any tenant) escalates to Backend Lead; a connector affecting more than one tenant simultaneously (framework-level bug, not adapter-specific) escalates to Chief Architect immediately as a potential P0.

---

## 11. Tenant Provisioning

**Trigger:** A new tenant signs up (self-service) or is provisioned by Sales/Program Director (assisted).

**Steps:**
1. Provisioning job (EPIC-04, idempotent) creates the `Tenant` record, seeds default Studio config from the assigned plan's template, creates the first admin user.
2. RLS policies apply automatically (they're table-level, not tenant-instance-level — no per-tenant policy creation step needed, this is why the RLS-everywhere investment in Phase 0 pays off here).
3. `Subscription` created in `trial` state (or `active` if sales-assisted with immediate payment).
4. Welcome/onboarding communication sent (email, tenant-facing checklist).

**Verification:** New tenant can log in, sees their entitled DOM/CAP surface correctly (per their plan), and is provably isolated from every other tenant (automated check against the cross-tenant adversarial suite for this specific new tenant ID).

**Rollback:** If provisioning fails partway, the idempotent job can simply be re-run — it does not create duplicate records on retry.

**Escalation:** A provisioning failure affecting the trial-to-active conversion path escalates to Backend Lead same-day (this is revenue-affecting).

---

## 12. Tenant Suspension

**Trigger:** Dunning workflow exhausts retries (non-payment), or a manual suspension is issued (Owner Console, e.g., for a Terms-of-Service violation).

**Steps:**
1. `Subscription.status` transitions to `suspended`.
2. Enforcement happens at **both** the API Gateway (reject write requests) and the application layer (read-only mode banner in the UI) — defense in depth, not just one layer.
3. Data is retained, untouched — suspension is not deletion.
4. Tenant is notified with a clear reactivation path (pay outstanding balance, or contact support for a manual suspension).

**Verification:** Suspended tenant's write endpoints return a clear "account suspended" response (not a generic 403); read access continues to work (so the tenant can see their own data and know why they're suspended).

**Rollback:** Reactivation (payment resolved, or manual override) reverses the suspension immediately — no data re-provisioning needed since nothing was deleted.

**Escalation:** A tenant disputing a suspension escalates to Program Director, who has authority to manually reactivate pending investigation.

---

## 13. Tenant Deletion

**Trigger:** Tenant-initiated deletion request, or churn past the defined retention window.

**Steps:**
1. Confirm the request is authenticated and authorized (the tenant's own admin, or an Owner-Platform action with documented justification).
2. Enter the retention window (PDPL-aligned, duration documented in `COMMERCIAL_LAUNCH_PLAN.md`/DPA) — data is soft-deleted (inaccessible to the tenant, retained for potential recovery/legal hold) but not yet purged.
3. At the end of the retention window, a scheduled job hard-deletes all tenant-scoped data across every table (verified against the same table list RLS was applied to — nothing gets missed because it's the same enumerated list).
4. Connector credentials (`ExternalSystemConnection.credential_ref`) are revoked at the vault immediately upon deletion request, not held through the retention window (credentials are a live security surface, unlike historical data).
5. Confirmation sent to the requester once hard deletion completes.

**Verification:** Post-hard-deletion, a query for the tenant's ID across every tenant-scoped table returns zero rows; audit log retains the deletion event itself (the deletion is logged, even though the data is gone).

**Rollback:** Only possible during the retention window (soft-delete phase) — a documented "undelete" procedure exists for that window only; hard deletion is irreversible by design and communicated as such to the tenant before they confirm the request.

**Escalation:** Any hard-deletion job failure (partial deletion across tables) is a P0 — it means either lingering PII exposure or a broken tenant record, both unacceptable; pages Backend Lead + Security immediately.

---

## 14. Database Role Provisioning (New Environment)

**Trigger:** Standing up Postgres for any new environment (a new staging host, a new production region, a rebuilt CI runner image, a new managed-Postgres target). R-14 (`docs/program/RISK_REGISTER.md`) — required before that environment carries real tenant data.

**Preconditions:** The environment's Postgres is reachable with the owner/migration role (`POSTGRES_USER`, default `salesos`) that every compose file and `railway.json` already provisions.

**Steps:**
1. If Postgres is started via one of this repo's compose files (`docker-compose.yml`, `docker-compose.prod.yml`, `infra/staging/docker-compose.staging*.yml`), no action is needed on a **fresh** data volume — `infra/docker/postgres/init/02-app-role.sql` is already mounted as `docker-entrypoint-initdb.d` alongside `01-init.sql` and runs automatically once, on first init.
2. If Postgres already has data (the common case — Postgres only executes `docker-entrypoint-initdb.d/` against an empty data directory), apply it manually and idempotently: `psql -U <owner_role> -d <db_name> -f infra/docker/postgres/init/02-app-role.sql`. Safe to re-run — the role-creation step is `IF NOT EXISTS`-guarded and every `GRANT`/`ALTER DEFAULT PRIVILEGES` statement is itself idempotent.
3. If Postgres is **not** started via one of these compose files (e.g. a managed provider's Postgres add-on, as with Railway — see `docs/program/RISK_REGISTER.md` R-14's environment matrix), there is no init-script mount to rely on; step 2's manual `psql` invocation must be run explicitly as part of that environment's provisioning/deploy process, and `APP_POSTGRES_PASSWORD` (see step 4) must be set through whatever secrets mechanism that platform uses.
4. Set `APP_POSTGRES_USER=salesos_app` and a unique `APP_POSTGRES_PASSWORD` (`openssl rand -hex 32`) in that environment's env/secrets store, matching the password set in step 1 or 2's role creation (`ALTER ROLE salesos_app WITH PASSWORD '...'` if it needs to differ from the SQL file's default). Leaving `APP_POSTGRES_PASSWORD` unset is safe — `app_database_url` (`app/config.py`) falls back to the owner-role `DATABASE_URL`, so a not-yet-provisioned environment is unprotected but never broken.
5. Verify with the bypass-probe: create a throwaway `FORCE ROW LEVEL SECURITY` table with a tenant-scoped policy, insert two tenants' rows, `SELECT` as the owner role (expect: both rows — owner roles bypass RLS by design) and as `salesos_app` (expect: only the session's own tenant). Identical mismatch behavior between the two roles confirms provisioning succeeded; identical (non-isolating) behavior under both means `salesos_app` isn't actually being used yet.

**Verification:** `SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'salesos_app'` returns `f, f`; the bypass-probe in step 5 isolates under `salesos_app`.

**Rollback:** Fully reversible — unset `APP_POSTGRES_PASSWORD` (or don't set it) to fall back to the owner role immediately, no redeploy of the role itself required. `DROP ROLE salesos_app` only if the role must be removed entirely (rare; harmless to leave provisioned-but-unused).

---

## 15. Owner Console (Platform Ops) — EPIC-07 / FE-S07

**Trigger:** Platform Ops/Support/CS need tenant status, plan, usage, or billing without opening a DB session.

**Preconditions:** Access to the SalesOS Next app `/admin/*` routes. A JWT with audience `salesos-owner-platform` is required for `/api/v1/admin/*` (DEC-093 / `owner_auth`). Tenant audience `salesos-api` tokens are rejected by admin APIs. **Owner login mint remains a BE follow-up — do not invent tokens or Stripe keys.**

**Steps:**
1. Open Owner Console overview at `/admin` (shell shows audience + host honesty; target host `owner.salesos.io` is named, not claimed as a live separate deploy).
2. Use shell nav or overview deep-links:
   - `/admin/tenants` — list + detail (status, plan, usage snapshot, billing panel).
   - `/admin/billing` — platform invoices, dunning, apply-pending plan changes, Stripe readiness booleans only.
3. If the audience banner warns about `salesos-api`, stop mutating admin APIs — mint path is not shipped; escalate to Backend for DEC-093 owner login when needed. FE-S07-06: a tenant-audience 401 on `/api/v1/admin/*` toasts honesty and **keeps** the tenant session (no forced `/login` bounce).
4. Shell also links Flags (`/admin/flags`), Config (`/admin/config`), and Audit (`/admin/audit`).
5. Prefer read-path Ops work in Phase 1. Existing lifecycle CTAs (suspend/activate/reprovision/delete) remain on tenants page; refund / ad-hoc suspend-override beyond those APIs are deferred.

**Verification:** Shell testids `owner-console-shell`, `owner-console-audience-banner`, `owner-console-host-banner` visible; tenants/billing pages load; admin API calls succeed only with owner audience.

**Rollback:** N/A (read UI). If a mistaken write occurred via lifecycle APIs, use the existing activate/reprovision/retention procedures in §§12–13.

**Escalation:** Audience/auth failures → Backend (owner mint / DEC-093). Billing 503 / Stripe unavailable → DevOps (env secrets; no invented keys). **Not Production GO.**

**Crumb:** [`PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md`](PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md).
