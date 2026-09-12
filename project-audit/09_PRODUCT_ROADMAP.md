# 09 — Product Roadmap — خارطة الطريق

**Scope:** 12 months, tied to the 3-layer strategy in `03_PRODUCT_STRATEGY.md` (Consolidate → Prove → Scale). Every item is either **evidence-anchored** (already coded/tested) or **RECOMMENDATION** (proposal).

---

## 1. Roadmap timeline (calendar view)

```
Q4 2026 ─ Consolidate ────────────── Q1 2027 ─ Prove ──────── Q2 2027 ──── Q3 2027 ─ Scale ────── Q4 2027
Repair · Reconcile · Legal · Backup · Phase 7 · DP MOU × 3 · Convert 1–2 to paid · Case study · SOC2 · 10 tenants
```

---

## 2. Q4 2026 (Oct–Dec 2026) — CONSOLIDATE

**Goal:** ship the honest MVP + sign 3 Design Partner MOUs.

| # | Item | Owner | Evidence path | Status |
|---|------|-------|--------------|--------|
| Q4-01 | Reconcile `feature_ai_copilot` + `AI_HONESTY.md` + `README.md` domain table | Founder | `config.py`, `AI_HONESTY.md`, `README.md` | pending |
| Q4-02 | Repair `fix/login-and-keys` git working tree | Founder | `git status` | pending |
| Q4-03 | Sign production LLM contract (OpenAI Enterprise / Azure OpenAI / hosted-KSA) | Founder | vendor MSA + Stripe/invoice | pending |
| Q4-04 | Enable Railway managed backup schedule | Founder + Railway | Railway dashboard evidence | pending |
| Q4-05 | Complete OAuth staging (Google Cloud Console) | Founder | live callback test | pending |
| Q4-06 | Provision Stripe live keys; publish pricing page (draft) | Founder + legal | live Stripe test invoice | pending |
| Q4-07 | Draft MSA + DPA + Order Form + SLA-lite + ToS | Legal + Founder | signed by legal | pending |
| Q4-08 | Public status page (uptime commit) + support email + response SLA | Founder | public URL | pending |
| Q4-09 | Deprecate legacy `(dashboard)` routes visibly | Founder | banner + telemetry event on legacy hits | pending |
| Q4-10 | Repository hygiene sprint: prune `.venv/`, `.mypy_cache_*`, `packages/packages/*`, `archive/archive/*`, `infrastructure/infrastructure/*` | Founder | commit + tree diff | pending |
| Q4-11 | Repo `.gitignore` audit + PII sweep | Founder | scanner run | pending |
| Q4-12 | Land 1 Design Partner MOU (signed) | Founder | signed MOU | pending |
| Q4-13 | Phase 7-B pilot execution for the DP's tenant subset (with human review + PO sign-off) | Data + PO + Founder | `PHASE7B_*` doc | pending |
| Q4-14 | Muhide subset ingestion into production `salesos` for DP tenant | DevOps + Data | `alembic current`, row count check | pending |
| Q4-15 | DP onboarding runbook execution (per `08_SALES_PLAYBOOK.md` §5) | Founder + fractional CS | onboarding checklist | pending |

---

## 3. Q1 2027 (Jan–Mar 2027) — PROVE

**Goal:** land 3 Design Partners → convert 1 to paid Team tier.

| # | Item |
|---|------|
| Q1-01 | Design Partners #2 and #3 signed |
| Q1-02 | Weekly HITL-approved recommendations tracked across all 3 tenants |
| Q1-03 | First case study drafted (DP #1) |
| Q1-04 | Convert DP #1 to Team-tier paid (SAR 60k) |
| Q1-05 | Effectiveness dashboard tuned to real customer KPIs |
| Q1-06 | Support runbook v1 (bilingual) |
| Q1-07 | External pentest scheduled (residual per FINAL_GO_NOGO) |
| Q1-08 | SOC2 Type I evidence pack drafted (leverage STORY-14-05) |
| Q1-09 | PDPL alignment statement drafted + reviewed |
| Q1-10 | Phase 7-B / 7-C human review workstream sustained (paid staff) |
| Q1-11 | Signal Marketplace: expand 1 pack (e.g., government-sector or retail) |
| Q1-12 | AI provider cost tuning — target ≤ SAR 60/seat/mo |

---

## 4. Q2 2027 (Apr–Jun 2027) — PROVE-continued

| # | Item |
|---|------|
| Q2-01 | 2 case studies published |
| Q2-02 | 3 paying tenants total (DP #2 and #3 converted) |
| Q2-03 | ARR ≥ SAR 300k |
| Q2-04 | External pentest completed; remediation done |
| Q2-05 | SOC2 Type I attestation completed |
| Q2-06 | First customer-referral acquired |
| Q2-07 | Attend 1 vertical event (Construction / Healthcare / FS) |
| Q2-08 | Muhide production ingestion completed for all 3 tenants |
| Q2-09 | ADR-108 v2 signal: keep Neo4j offline OR activate KG for VC ICP |
| Q2-10 | Hire: 1 senior FE + 1 senior data engineer (after case study #1 published) |

---

## 5. Q3 2027 (Jul–Sep 2027) — SCALE-begin

| # | Item |
|---|------|
| Q3-01 | 6 paying tenants |
| Q3-02 | ARR ≥ SAR 700k |
| Q3-03 | Hire: Head of Sales (KSA-based) |
| Q3-04 | First Business-tier customer (SAR 180k) |
| Q3-05 | Signal Marketplace expanded to 5 packs |
| Q3-06 | Referral program launched for paid tenants |
| Q3-07 | Studio adoption: at least 3 tenants author custom scoring rules / prompt library |
| Q3-08 | Data residency posture: if KSA-hosted Postgres available on Railway or partner, migrate for Enterprise-tier readiness |

---

## 6. Q4 2027 (Oct–Dec 2027) — SCALE

| # | Item |
|---|------|
| Q4-01 | 10 paying tenants total |
| Q4-02 | ARR ≥ SAR 1.5M |
| Q4-03 | First Enterprise-tier tenant (SAR 500k+) — likely with VPC deployment |
| Q4-04 | K8s deployment path un-quarantined for Enterprise VPC (per updated DEC-149 review) |
| Q4-05 | Hire: 2 AEs + 1 SDR |
| Q4-06 | Vertical productization first pass: `SalesOS for VC Deal Flow` (requires KG activation) |
| Q4-07 | Series A discussion (data room + case studies + ARR + retention proof) |

---

## 7. Feature-level backlog (12-month view)

### Core product (v3 shell)
- v3 Home / dashboard polish
- Companies list: bulk import, saved views, tags
- Contact enrichment with cited sources
- Deal 360: full evidence trail widget
- Pipeline: Kanban toggle (behind `feature_crm_kanban` flag)
- Activities: cross-links to Comm Hub emails/meetings
- Revenue: signed-in Territory + Quota editor
- Proposals: PDF export via real generator (not stub) — this is a Phase 1 residual
- Reviews: multi-step approval configurator
- Approvals: SLA aging + escalation UI
- Analytics: cohort/funnel export
- Effectiveness: signal-to-outcome attribution UI

### Master Data / ER
- Review Queue tenant-scoped filters + saved decisions
- Fuzzy pair reviewer keyboard shortcuts
- Provenance viewer (all evidence tracks per record)
- CR history UI (with SUSPICIOUS_SHORT flagging)
- Person↔Company relationship auditor UI

### Copilot / AI
- Model tier per tenant configurator (Studio)
- Prompt Library authoring + versioning
- AI Policy Studio (data-class rules, model tier caps)
- Governance Audit viewer for admins
- Groundedness score display in Copilot answers

### Integrations
- Comm Hub: Calendar sync UI polish
- Comm Hub: Outlook (post-Gmail success)
- Notion sync UI: last-sync + errors
- Odoo integration (post-signal, not before)

### Platform
- Sentry DSN + live error stream
- OpenTelemetry deployment
- Multi-region DR (post-Enterprise sale)
- K8s un-quarantine (post-Enterprise sale)

### Studio (Tenant Studio)
- All 10 studio sub-modules polished (prompt-library, ai-policies, ai-memory, custom-fields, workflows, scoring, permissions, territories, branding, notifications)
- Studio onboarding wizard

---

## 8. Parked / dropped (do not build in 2027)

- Mobile app
- Public developer marketplace
- White-label mode
- Non-Arabic non-English UI
- Non-Saudi geography
- AuditOS / DecisionOS / LocalContentOS
- Autonomous AI (auto-execute)
- Public LLM chat mode (no HITL)

---

## 9. Release cadence & gate discipline

- Follow `SALESOS_MASTER_CLOSURE_SEQUENCE.md`: build → prove → close gate → advance
- Every quarter: one signed evidence pack (like Phase 1/2/3/4 packs)
- Every month: session summary in `AGENTS.md`
- Every week: `UpdateCurrentStep` for parent agent orchestration

---

## 10. Roadmap failure conditions (trigger revisit)

Revisit the roadmap **immediately** if any of these fires:
- 90 days into Q4 2026 with 0 signed Design Partner MOUs
- 180 days into Q1–Q2 2027 with 0 paid conversions
- Copilot hallucination incident in a customer environment
- Data breach or tenant leak
- KSA regulatory change (PDPL, SAMA, NCA) requiring architectural rework
- Founder burnout signals (agreed protective threshold with board)
- Runway < 6 months without a signed funding term sheet

---

*Roadmap — calendar-anchored, evidence-cited. See `10_KPI_FRAMEWORK.md` for what to measure weekly.*
