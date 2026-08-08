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

## 2. Release Status — ACTIVE

> **ACTIVE.**

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
