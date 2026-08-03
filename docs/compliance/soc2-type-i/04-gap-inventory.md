# 04 — Gap inventory (STORY-14-05)

> **Purpose:** Explicit residuals so Program Director / auditor know what this pack does **not** close.  
> **Honesty:** Assembled evidence pack ≠ Type I certified.

## Closed by this pack (in-repo assembly only)

| Item | Status |
|------|--------|
| Audit logging / access review / change management **index** | **CLOSED (evidence pack)** — light validated assembly |
| Pointers to DevOps tip-line CI/Deploy/Security Scan @ `4754b8b` | Linked |
| Pointers to BE audit/headers/rate-limit/CSRF/RLS hooks (`d0070fa`) | Linked |
| Honest non-claim of auditor Type I | Stated throughout |

## Residual — Program Director

| # | Gap | Why it matters | Suggested next |
|---|-----|----------------|----------------|
| PD-1 | No signed quarterly access-review worksheets in-repo | CC6 access | Run first review; store offline (PII) |
| PD-2 | No CAB / change-ticket archive mapped to deploys | Change mgmt completeness | Map tip SHAs ↔ tickets |
| PD-3 | Branch protection / required-review org settings not captured | SDLC control | Screenshot + date into auditor folder |
| PD-4 | Customer / prospect language risk | Sales overclaim | Approve “evidence underway / Type I audit post-GA” wording only |
| PD-5 | RC soak / Production GO unrelated | Scope creep | Keep forbidden per board hub |

## Residual — Ops / DevOps

| # | Gap | Label |
|---|-----|-------|
| OPS-1 | Live proof audit retention ≥90d on published env (export sample) | **not validated** / may be **residual-external** |
| OPS-2 | Central SIEM / immutable log ship | **gap** |
| OPS-3 | On-call / IR drill evidence dated for Type I window | **not validated** (plan exists: `INCIDENT_RESPONSE_PLAN.md`) |
| OPS-4 | Stage 6 GHCR still quarantined | **SKIPPED** by design — cite DEC-150 B; do not “fix” by un-quarantining for SOC2 |

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

## Board acceptance mapping

| Sprint-25 AC fragment | Pack disposition |
|-----------------------|------------------|
| Audit logging evidence assembled | **Yes** — `01-audit-logging.md` |
| Access review evidence assembled | **Yes** — process + gaps in `02-access-review.md` (samples = PD residual) |
| Change management evidence assembled | **Yes** — `03-change-management.md` + DevOps URLs |
| Type I audit itself | **post-GA residual-external** — unchanged |
