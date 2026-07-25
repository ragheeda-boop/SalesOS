# Blocker Classification

**Classification taxonomy:**

| Category | Code | Rule |
|----------|------|------|
| Missing Evidence | **A** | Work CLAIMED done but no machine artifact proving it |
| Missing Execution | **B** | Scripts/tools exist but have NOT been run (or run incomplete) |
| Missing Infrastructure | **C** | Requires cloud/VPS/GitHub/CI infrastructure not currently available |
| Missing Security Validation | **D** | Requires external pentest, security audit, or signed acceptance |
| Governance | **E** | Requires human decision, signature, or approval |
| External Dependency | **F** | Requires third-party service, external system, or production access |

---

## Complete classification matrix

| ID | Blocker | Cat A | Cat B | Cat C | Cat D | Cat E | Cat F | OpenCode? |
|----|---------|-------|-------|-------|-------|-------|-------|-----------|
| B1 | 48-72h soak incomplete | | **B** | | | | | PARTIAL |
| B2 | Cloud staging blocked | | | **C** | | | | NO |
| B3 | Prod Alembic not executed | | **B** | | | **E** | **F** | NO |
| B4 | CTO/TL signatures unsigned | | | | | **E** | | NO |
| B5 | No staging pentest | | | | **D** | | | NO |
| B6 | pg_dump/restore no machine evidence | **A** | **B** | | | | | **YES** |
| B7 | Pytest ~1542 not logged | **A** | **B** | | | | | **YES** |
| B8 | FE lint/tsc/build no standalone logs | **A** | **B** | | | | | **YES** |
| B9 | Observability not exercised | | **B** | | | | | **YES** |
| B10 | WAL/PITR + offsite not proven | **A** | **B** | **C** | | | | PARTIAL |
| B11 | RPO acceptance unsigned | | | | | **E** | | NO |
| B12 | AI honesty human PRC open | | | | | **E** | | NO |
| B13 | Launch hygiene (freeze/on-call) | | **B** | | | **E** | | NO |
| B14 | Crawl screenshots null | **A** | **B** | | | | | **YES** |
| B15 | Security scanners not run | **A** | **B** | | | | | **YES** |
| B16 | Alembic upgrade transcript missing | **A** | **B** | | | | | **YES** |
| B17 | Auth contract probes not archived | **A** | **B** | | | | | **YES** |

---

## Category summary

| Category | Count | Blocker IDs |
|----------|-------|-------------|
| **A — Missing Evidence** | 8 | B6, B7, B8, B10, B14, B15, B16, B17 |
| **B — Missing Execution** | 9 | B1, B6, B7, B8, B9, B10, B13, B14, B15, B16, B17 |
| **C — Missing Infrastructure** | 2 | B2, B10 |
| **D — Missing Security Validation** | 1 | B5 |
| **E — Governance** | 5 | B3, B4, B11, B12, B13 |
| **F — External Dependency** | 1 | B3 |

Note: Blockers can belong to multiple categories. B3 has both E (governance — requires approval to execute) and F (external — requires production DB connection).

---

## Dependency graph

```
B4 (Signatures)  ──┐
B11 (RPO)        ──┤
B12 (AI PRC)     ──┤─── Governance prerequisites for B3 and GO
B13 (Launch)     ──┘
                    │
B2 (Cloud staging) ─┼─── Infrastructure prerequisite for B3
                    │
B5 (Pentest)      ──┤─── Security prerequisite for B3
                    │
B1 (48h soak)     ──┤
B6 (pg_dump)      ──┤─── Evidence prerequisites for B3
B7 (Pytest)       ──┤
B10 (WAL/PITR)    ──┘
                    │
                    v
              B3 (Prod Migrate) ─── Production GO
```

---

## Autonomy assessment

| Can OpenCode execute autonomously? | Count | Details |
|------------------------------------|-------|---------|
| **YES** | **8** | B6, B7, B8, B9, B14, B15, B16, B17 |
| **PARTIAL** | **2** | B1 (can start 48h soak, cannot wait 48h), B10 (local WAL yes, S3 no) |
| **NO** | **7** | B2, B3, B4, B5, B11, B12, B13 |

---

## Owner assignment

| Blocker | Owner | Rationale |
|---------|-------|-----------|
| B1 — 48h soak | **OpenCode + Ops** | Start soak script; ops monitors termination |
| B2 — Cloud staging | **DevOps / Infra** | Needs GitHub Environment + VPS credentials |
| B3 — Prod migrate | **DBA / Tech Lead** | Requires production DB access + approval |
| B4 — Signatures | **CTO / Tech Lead** | Human decision |
| B5 — Pentest | **Security / External** | Third-party or internal security team |
| B6 — pg_dump evidence | **OpenCode** | Existing scripts; needs Docker running |
| B7 — Pytest evidence | **OpenCode** | Docker-based pytest runner |
| B8 — FE toolchain logs | **OpenCode** | Run lint/tsc/build; save logs |
| B9 — Observability exercise | **OpenCode** | Docker compose --profile observability |
| B10 — WAL/PITR | **OpenCode (local) + DevOps (S3)** | Local drill automatable; S3 needs infra |
| B11 — RPO acceptance | **CTO** | Human decision |
| B12 — AI PRC | **CTO / Product** | Human review |
| B13 — Launch hygiene | **Tech Lead / Ops** | Operational planning |
| B14 — Screenshot crawl | **OpenCode** | Re-run crawl with screenshot capture |
| B15 — Security scan | **OpenCode** | Run existing scanner scripts |
| B16 — Alembic transcript | **OpenCode** | Re-run upgrade with log capture |
| B17 — Auth probes | **OpenCode** | Run smoke-auth.ps1; save evidence |
