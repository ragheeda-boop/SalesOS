# Production Readiness Checklist

> **How to use this document:** every row has a measurable acceptance criterion, not a subjective judgment call. "Mandatory for GA" rows must ALL be checked before `MASTER_EXECUTION_PLAN.md` §9 Exit Criterion 1 is considered satisfied. "Post-GA acceptable" rows are named and tracked, not silently ignored.
> **Verification owner** column names who signs off — this is a checklist with accountability, not a wishlist.

## Architecture

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Two-plane separation (Owner/Tenant) enforced | Owner JWT rejected by 100% of tenant-scoped endpoints and vice versa, tested automatically in CI | Yes | Chief Architect |
| `SourceConnector` interface has zero adapter-specific leakage | Code review confirms no Odoo-specific (or 2nd-connector-specific) symbol exists outside its own adapter module | Yes | Chief Architect |
| Entitlement Engine gates 100% of DOM/CAP surface | Full plan × capability matrix test, zero bypass findings | Yes | CTO |
| RLS policy present on 100% of tenant-scoped tables | Schema-lint CI check, zero missing | Yes | Chief Architect |
| No hard dependency on Kafka in any critical path | Code audit confirms Outbox/Postgres-based mechanism used wherever Kafka would otherwise be load-bearing | Yes | Chief Architect |
| No user-facing feature depends on Neo4j being populated | Feature audit — graph population additive/best-effort only | Yes | Chief Architect |
| Sharding-by-tenant-cohort | N/A — explicitly deferred | **Post-GA acceptable** | Chief Architect |

## Performance

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| API p95 latency, core CRM endpoints | ≤300ms at 50-simulated-tenant load | Yes | DevOps/SRE |
| API p99 latency, core CRM endpoints | ≤800ms at 50-simulated-tenant load | Yes | DevOps/SRE |
| Company 360 page load (server-rendered data ready) | ≤1.5s p95 | Yes | Frontend Lead |
| Connector sync throughput | ≥5,000 records/hour sustained per connection, matching the real observed 27,264-record Odoo scale within a single scheduled window | Yes | Backend Lead |
| Entitlement cache propagation on plan change | ≤60 seconds from change to enforcement | Yes | Backend Lead |
| Frontend bundle size (initial load) | ≤500KB gzipped for the tenant app shell | Yes | Frontend Lead |
| Sustained load test duration | 2 hours at 50 simulated tenants, no degradation trend | Yes | DevOps/SRE |

## Security

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Decision Center IDOR | Fixed, regression-tested, independently reviewed | Yes | Security |
| Webhook SSRF | URL allowlist live, regression-tested | Yes | Security |
| CSRF bypass via `X-API-Key` | Fixed, regression-tested | Yes | Security |
| External penetration test | Zero unresolved criticals; all highs triaged with fix-by date or documented risk acceptance signed by CTO | Yes | Security |
| Cross-tenant adversarial test suite | 100% pass across every tenant-scoped table and every Integration Hub/Studio table added since Phase 0 | Yes | Security |
| Credential encryption (connectors, AI providers) | Fernet (or equivalent) at rest, `credential_ref` pointer pattern, zero raw secrets in any JSONB config column | Yes | Security |
| Secrets rotation process | Documented and exercised at least once (not just written) | Yes | DevOps/SRE |
| SOC2 Type II | N/A — Type I evidence only at GA | **Post-GA acceptable** | Security |
| GDPR full compliance | N/A — PDPL-aligned scope only at GA | **Post-GA acceptable** | Security |

## AI

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Mock-data elimination | 11/11 AI agents running on real tenant data paths in production | Yes | AI Lead |
| PII scrubbing before RAG ingestion | Verified against real production note samples (phone numbers, names) with zero leakage found in a manual audit sample of ≥100 records | Yes | AI Lead |
| Per-plan token ceiling enforcement | Starter/Growth/Enterprise ceilings enforced, tested against a deliberate over-limit scenario | Yes | AI Lead |
| AI provider failover | Engages within 30 seconds of primary provider unavailability, tested in a chaos drill | Yes | AI Lead |
| LLM regression suite | Baseline established, detects a deliberately-injected quality regression in a test run — **CI/non-prod harness landed** (`/api/v1/chaos/llm-regression`; crumb `PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`). Live continuous provider-watch = Ops residual. `feature_ai_copilot=False`; not live LLM GO | Yes | AI Lead |
| AI Memory cross-tenant isolation | Adversarial test suite passes, including shared-provider-cache leakage scenarios | Yes | AI Lead |
| Cross-session long-term AI Memory | N/A — conversation-level only at GA | **Post-GA acceptable** | AI Lead |

## Integrations

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Odoo adapter production soak | 14+ consecutive days, zero unresolved P0 sync failures | Yes | Backend Lead |
| Second connector production soak | 14+ consecutive days, zero unresolved P0 sync failures, certified by an engineer other than `OdooAdapter`'s author | Yes | Backend Lead |
| Field-mapping drift detection | Fires correctly on a simulated field rename, does not silently null data | Yes | Backend Lead |
| Conflict resolution write-back exclusion | SalesOS-authored fields verified never read back as fresh source data, dedicated test | Yes | Backend Lead |
| Webhook-based connector path | Enabled only after SSRF/CSRF fixes re-verified against this specific caller | Yes | Security |
| Third-party marketplace connectors (external submitters) | N/A — first-party only at GA | **Post-GA acceptable** | CPO |

## Database

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Alembic migration state | Head matches models exactly, zero drift | Yes | Backend Lead |
| Composite indexes on new tenant-scoped tables | `(tenant_id, updated_at)` minimum on every table added since Phase 1 | Yes | Backend Lead |
| Monthly partitioning on high-volume tables | Applied to `TimelineEvent`/`InteractionNote` extension and `SyncRun` from creation | Yes | Backend Lead |
| Connection pooling tuned for target tenant concurrency | Verified under the 50-tenant load test with no connection exhaustion | Yes | DevOps/SRE |
| Query performance regression gate | No query added since Phase 0 exceeds 100ms p95 in isolation, tested via query-level profiling | Yes | Backend Lead |

## Backups

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Automated daily backups | Running, verified via successful restore test, not just "job completed" logs | Yes | DevOps/SRE |
| Backup retention policy | Documented (e.g., 30 daily + 12 monthly), enforced by automation, not manual cleanup | Yes | DevOps/SRE |
| Point-in-time recovery | Demonstrated to a timestamp within the last 24 hours, in the DR drill | Yes | DevOps/SRE |
| Cross-region backup replication | N/A unless a signed Enterprise deal requires it | **Post-GA acceptable** (unless contractually forced earlier) | DevOps/SRE |

## Monitoring

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Platform Health rollup (CAP-074) live | Cross-tenant dashboard shows uptime/latency/error-budget in real time | Yes | DevOps/SRE |
| Per-tenant resource consumption visible | Noisy-neighbor detection alert fires correctly in a simulated overload test | Yes | DevOps/SRE |
| Alert dry-run | Every production alert has been deliberately triggered at least once pre-GA to confirm it actually fires and reaches the right on-call channel | Yes | DevOps/SRE |
| SLO dashboards | Uptime, latency, error rate visible and matching `MASTER_EXECUTION_PLAN.md` §8 Success Criteria targets | Yes | DevOps/SRE |

## Logging

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Audit log completeness | Every tenant-data-touching admin/support action (including impersonation grants) is logged with actor, timestamp, and scope | Yes | Security |
| Log retention | Meets the SOC2 Type I evidence window (minimum 90 days) | Yes | DevOps/SRE |
| No secrets in logs | Verified via a log-scrubbing audit sample — API keys, tokens, credentials never appear in plaintext log output | Yes | Security |
| Structured logging across all new Phase 1-6 services | 100% of new services emit structured (not free-text) logs, verified by log-schema lint in CI | Yes | Backend Lead |

## Disaster Recovery

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| RTO (Recovery Time Objective) | ≤4 hours, measured in the Phase 6 DR drill | Yes | DevOps/SRE |
| RPO (Recovery Point Objective) | ≤1 hour, measured in the Phase 6 DR drill | Yes | DevOps/SRE |
| DR runbook exercised | At least once, with a written postmortem, before GA | Yes | DevOps/SRE |
| Multi-region active-active failover | N/A — active-passive sufficient at GA scale | **Post-GA acceptable** | DevOps/SRE |

## CI/CD

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Green build on `main` | 100% pass rate for 14 consecutive days pre-GA | Yes | QA Lead |
| New-code coverage gate | Enforced and blocking since Sprint 2, zero bypasses in the last 30 days pre-GA | Yes | QA Lead |
| Contract test suite | Covers 100% of externally-facing API surface added since Phase 1 | Yes | QA Lead |
| Automated rollback capability | A deploy can be reverted via a single documented command/pipeline action, tested at least once | Yes | DevOps/SRE |
| Blue/green or canary deploy mechanism | Live, used for the GA cutover itself | Yes | DevOps/SRE |

## Infrastructure

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Pooled multi-tenant tier proven at target scale | 50 simulated tenants sustained, per load test | Yes | DevOps/SRE |
| Siloed/dedicated-tenant tier | N/A at GA (A6 assumption) | **Post-GA acceptable** (unless an Enterprise deal forces it earlier) | DevOps/SRE |
| Secrets vault in production | Live, all connector/AI-provider credentials migrated off any interim storage | Yes | DevOps/SRE |
| Data residency enforcement (`Tenant.region`) | At least one non-default region path tested end-to-end, even if only one region is live at GA | Yes | DevOps/SRE |

## Compliance

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| PDPL-aligned data handling | Retention/deletion policy documented and enforced by the tenant deletion workflow (EPIC-04) | Yes | Security |
| SOC2 Type I evidence collection | **CLOSED (evidence pack)** — `docs/compliance/soc2-type-i/` + crumb `PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md`. Type I **audit** = post-GA. AI honesty indexed: `feature_ai_copilot=False`, Decision STUB, `AI_HONESTY.md` | Yes | Security |
| SOC2 Type I audit completed | N/A — Type I audit itself is post-GA | **Post-GA acceptable** | Security |
| Data Processing Agreement (DPA) template | Drafted and legally reviewed, available for Enterprise contracts | Yes | CPO / Legal (external) |

## Documentation

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| `OPERATIONS_MANUAL.md` runbooks | Every runbook exercised at least once in a drill, not just written | Yes | DevOps/SRE |
| Tenant-facing Studio help docs | Reviewed by Customer Success (or Program Director if CS not yet staffed) before Public Beta | Yes | CPO |
| API documentation (OpenAPI) | Matches actual API surface, verified by contract tests, not manually maintained prose | Yes | Backend Lead |
| `CANONICAL_ARCHITECTURE.md` v2.0.0 | Updated per `SAAS_PLATFORM_ARCHITECTURE.md` §17 diff list, merged before GA | Yes | Chief Architect |

## Support

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Support tiers defined | Starter/Growth/Enterprise SLA response times published (see `COMMERCIAL_LAUNCH_PLAN.md`) | Yes | CPO |
| Support staffing | At least 1 dedicated Customer Success hire onboarded before Public Beta | Yes | CPO |
| Support console (CAP-075) live | Impersonation grants audited, time-boxed, tenant-consent-gated | Yes | Backend Lead |
| 24/7 P0 on-call rotation | Established and tested with at least one dry-run page before GA | Yes | DevOps/SRE |

## Marketplace

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Certification pipeline | Processes a real listing end-to-end and correctly rejects an intentional negative test | Yes | Backend Lead |
| ≥3 connector listings + ≥1 playbook listing | Live and installable | Yes | CPO |
| Third-party submission intake | N/A at GA | **Post-GA acceptable** | CPO |

## Licensing

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| Entitlement Engine | Zero bypass findings across the full plan × capability matrix | Yes | Backend Lead |
| Billing integration | 20-transaction sandbox soak passed; production mode processing real charges for Partner Beta cohort | Yes | Backend Lead |
| Proration correctness | Every upgrade/downgrade direction tested | Yes | Backend Lead |
| Dunning workflow | Failed-payment → grace period → auto-suspend verified with zero manual steps | Yes | Backend Lead |

## Tenant Isolation

| Item | Acceptance Criteria | Mandatory for GA? | Verification Owner |
|---|---|---|---|
| RLS on 100% of tenant-scoped tables | Schema-lint CI enforced | Yes | Chief Architect |
| Cross-tenant adversarial suite | 100% pass, run on every PR, not just pre-GA | Yes | Security |
| Owner/Tenant JWT audience separation | Verified via automated cross-audience rejection test | Yes | Security |
| AI Memory isolation | Adversarial test passes, including provider-cache leakage scenarios | Yes | AI Lead |
| Support impersonation audit trail | 100% of impersonation sessions logged with consent record | Yes | Security |
