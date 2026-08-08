# SalesOS Release Governance Decision — 2026-08-07

| Field | Value |
|-------|-------|
| **Type** | Official project-owner governance decision |
| **Effective Date** | 2026-08-07 |
| **Decision Maker** | Project Owner (sole decision-maker; no separate CTO/Tech Lead role) |
| **Status** | **ACTIVE** — governs until superseded by an explicit owner decision |
| **Authority** | Supersedes prior CTO/Tech Lead governance framing for this project (single-owner reality) |

---

## 1. Engineering Status — CLOSED

> **CLOSED.**

- No new development may be added unless it is a **true P0** (production-blocking defect / security incident).
- Feature work, refactoring, dependency upgrades, and documentation sprawl are deferred.
- Exceptions require an explicit Project Owner decision.

---

## 1A. P0 Definition (project-specific, authoritative)

> A **P0 Release Blocker** is any item that leads to **one or more** of:

1. **Unauthorized access** (access-control bypass, privilege escalation, owner/tenant boundary crossing).
2. **Broken Tenant Isolation** (cross-tenant read/write, or the **inability to verify** isolation on the deployed environment).
3. **Data loss** (permanent destruction or corruption of production data).
4. **Loss of recoverability** (RPO/RTO breach, broken WAL/PITR/offsite chain).
5. **Service outage** (production downtime beyond the defined tolerance).
6. **Evidence tampering** (fabricated, forged, or falsified audit/verification evidence).
7. **Production with incorrect data** (deploying/releasing while data integrity is unverified or wrong).
8. **Governance bypass** (releasing without the mandatory human decision, freeze violation, or unreviewed change).

- P0 items **block GA** until resolved or explicitly accepted (with residual) by the Project Owner.
- Non-P0 items never block GA; they go to the post-GA backlog.
- The P0 status of an item is **assigned by the Project Owner**, not by AI.

### Currently assigned P0 Release Blockers

| # | Item | Evidence | Owner status |
|---|------|----------|--------------|
| P0-01 | **Tenant isolation / roles unverified on prod** — both accounts share tenant `326e0825`; cross-tenant test INCONCLUSIVE; roles swapped (`muhide.com`=user, `ratlfintech.com`=admin) | `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` §3.7 + §2 | **Assigned 2026-08-07** — to be handled inside RC-06 maintenance window (not vNext). See RC-06 scope + COUNTDOWN.md. |
| P1-window | **Frontend deployment drift** — prod runs `4750038`; repo HEAD `2538a7d` (4 commits: ADR-102, UX Phase 1, Company 360, Copilot activation) | `git log 4750038..HEAD` | **Owner decision 2026-08-08** — deploy HEAD inside RC-06 window (not now, freeze respected). |
| P1-window | **Honesty banners shown to end users** ("Not Production GO / RAG GO") | `salesos/frontend/src/**/*Honesty.ts` | **Owner decision 2026-08-08** — restrict to admin-only rendering (P1 window task, not a GA blocker). |

---

## 2. Release Status — ACTIVE (Release Operations Mode)

> **ACTIVE — Release Operations Mode** (owner decision 2026-08-07).

The project has formally exited **Development Mode** and entered **Release Operations Mode**:

- Any new work (CVP, ZAP, Chaos, OPA, Schemathesis, etc.) starts **only after Production GA**, per `docs/vnext/verification-platform/` roadmap.
- Development is declared **ended** until GA. The only work order is §4 below.

Full focus on:

- **Soak** (running until `2026-08-10T14:10Z`)
- **Evidence** (deposits, verification, probes)
- **Governance** (RC decisions, reconciliation, board)
- **Maintenance Window** (15 migrations + owner-login release)
- **Production GA** (owner decision)

## 3. Change Freeze

- Freeze active until **`2026-08-10T14:10Z`** OR official soak closure, whichever is earlier.
- During freeze: no code deploys to prod, no new feature commits, no dependency changes.

---

## 4. Post-soak sequence (the ONLY approved work order)

No new work opens after soak. Fixed order:

| Phase | Action | Output |
|-------|--------|--------|
| **1** | Close soak | `SOAK-COMPLETION-REPORT.md` |
| **2** | Review evidence → close RC-06 → RC-08 → remaining RC-01…05 | Signed decisions |
| **3** | Open maintenance window → execute 15 migrations → smoke tests → verification | Migration report |
| **4** | Owner Decision → **Production GA** | GA decision + archive |

> **P0-01 integration:** the maintenance window (Phase 3) must also resolve **P0-01** — decide role intent (`muhide.com` vs `ratlfintech.com`), decide tenant topology for `326e0825`, provision a cross-tenant test account if topology is split, and **re-run the cross-tenant isolation test** (audit §5 actions 1/2/5). GA is blocked until P0-01 is either resolved or explicitly accepted with residual by the Project Owner.

> **Daily tracker:** [`COUNTDOWN.md`](./COUNTDOWN.md) is the pre-launch page — open each morning until GA; tracks T-72h → Maintenance → GA with owner-assigned "Done?" per marker.

---

## 5. Release Archive mandate

An **immutable Release Archive** must be created at `docs/releases/v1.0.0-ga/`:

```
releases/v1.0.0-ga/
  evidence/     — prod health, WAL/PITR, auth/RBAC audit JSONs
  governance/   — reconciliation pack, DOC-CONTRADICTIONS, DOC-MAP
  reports/      — EAB run reports, exec brief, audit reports
  cutover/      — cutover package, maintenance window package
  decisions/    — RC decision packet (RC-01…08)
  signatures/   — SIGN_HERE, go-live signature packet
  soak/         — soak completion report + loop evidence index
```

Rules:

- **Immutable copies** — never edited after deposit. The archive is a **Release Record** independent of ongoing operational doc evolution.
- The archive is populated at GA; nothing inside is rewritten when source docs evolve.
- New releases get their own directory (`v1.0.1`, …) — prior release dirs never mutate.

---

## 6. Governance terminology rule

For a **single-owner project**, all references where "CTO" / "Tech Lead" meant the owner's **personal decision** are replaced by:

- **Project Owner Decision**
- **Project Owner Acceptance**

Rationale: avoids form-governance that simulates roles that do not exist. If the team grows later, responsibilities redistribute to named people without changing process essence.

Scope note: historical EAB run archives (`history/EAB-*`) and external/third-party audit docs keep their original labels (they are records, not current operating docs).

---

*Recorded by executor (AI) per owner instruction 2026-08-07. This is an owner decision record; AI does not make decisions.*
