# 04 — Gap inventory (STORY-14-05)

> **Purpose:** Explicit residuals so Program Director / auditor know what this pack does **not** close.  
> **Honesty:** Assembled evidence pack ≠ Type I certified.  
> **PD templates:** **LANDED** (`06`–`09`) · signatures / screenshots / live export = **still residual**.

## Closed by this pack (in-repo assembly only)

| Item | Status |
|------|--------|
| Audit logging / access review / change management **index** | **CLOSED (evidence pack)** — light validated assembly |
| Pointers to DevOps tip-line CI/Deploy/Security Scan @ `4754b8b` | Linked |
| Pointers to BE audit/headers/rate-limit/CSRF/RLS hooks (`d0070fa`) | Linked |
| PD worksheet / CAB / branch-protection / 90d-export **templates** | **LANDED** — unsigned (`06`–`09`) |
| Honest non-claim of auditor Type I | Stated throughout |

## Residual — Program Director

| # | Gap | Why it matters | Suggested next | Template |
|---|-----|----------------|----------------|----------|
| PD-1 | No **signed** quarterly access-review worksheets | CC6 access | Run first review; store offline (PII) | [`06-access-review-worksheet-template.md`](./06-access-review-worksheet-template.md) **LANDED** · signatures residual |
| PD-2 | No **filled** CAB / change-ticket archive mapped to deploys | Change mgmt completeness | Map tip SHAs ↔ tickets; sign period | [`07-cab-deploy-mapping-template.md`](./07-cab-deploy-mapping-template.md) **LANDED** · filled archive residual |
| PD-3 | Branch protection / required-review org settings not **captured** | SDLC control | Screenshot + date into auditor folder | [`08-branch-protection-evidence-checklist.md`](./08-branch-protection-evidence-checklist.md) **LANDED** · screenshots residual |
| PD-4 | Customer / prospect language risk | Sales overclaim | Approve “evidence underway / Type I audit post-GA” wording only | N/A (policy) |
| PD-5 | RC soak / Production GO unrelated | Scope creep | Keep forbidden per board hub | N/A |

## Residual — Ops / DevOps

| # | Gap | Label | Runbook |
|---|-----|-------|---------|
| OPS-1 | Live proof audit retention ≥90d on published env (export sample) | **not validated** / may be **residual-external** | [`09-audit-log-export-90d-runbook.md`](./09-audit-log-export-90d-runbook.md) **LANDED** · live sample residual |
| OPS-2 | Central SIEM / immutable log ship | **gap** | — |
| OPS-3 | On-call / IR drill evidence dated for Type I window | **not validated** (plan exists: `INCIDENT_RESPONSE_PLAN.md`) | — |
| OPS-4 | Stage 6 GHCR still quarantined | **SKIPPED** by design — cite DEC-150 B; do not “fix” by un-quarantining for SOC2 | — |

## Residual — Security / auditor (external)

| # | Gap | Label |
|---|-----|-------|
| AUD-1 | Formal SOC2 Type I examination by CPA firm | **post-GA residual-external** (A5) |
| AUD-2 | Auditor-ready TSC matrix with control owners + test procedures | This pack is a **sketch** only (`05-controls-mapping.md`) |
| AUD-3 | Population completeness testing of audit events | **not validated** |
| AUD-4 | STORY-14-04 external pentest / zero criticals | Separate story — **do not invent** here |
| AUD-5 | Staging SSRF tabletop still OPEN per BE crumb | Security 14-04 residual |
| AI-1 | Live LLM / continuous provider quality watch | **Ops residual** — 14-07 is CI/fixture harness only; `feature_ai_copilot=False`; Decision **STUB** |

## Forbidden claims checklist

- [ ] Do **not** say “SOC2 Type I certified”
- [ ] Do **not** say “Type I audit complete”
- [ ] Do **not** say “Production GO”
- [ ] Do **not** treat Stage 6 skip as unexplained control failure
- [ ] Do **not** claim Type II
- [ ] Do **not** claim live LLM GO / “AI-native GA” / Decision STUB as production AI
- [ ] Do **not** treat unsigned templates as executed control samples

## Board acceptance mapping

| Sprint-25 AC fragment | Pack disposition |
|-----------------------|------------------|
| Audit logging evidence assembled | **Yes** — `01-audit-logging.md` (+ runbook `09` template) |
| Access review evidence assembled | **Yes** — process + gaps in `02-access-review.md` (signed samples = PD residual; template `06` LANDED) |
| Change management evidence assembled | **Yes** — `03-change-management.md` + DevOps URLs (CAB fill = PD residual; templates `07`/`08` LANDED) |
| Type I audit itself | **post-GA residual-external** — unchanged |
