# Stream D — M1 Status (Security Prove)

**Stream:** D — Security Prove  
**Milestone:** M1 (first full parallel wave)  
**Date:** 2026-08-08  
**Charter:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Board refs:** CP-D-01 · CP-D-02 · CP-D-03 · CP-REL-05 · CP-REL-10  

**Principle:** AI assists. Humans decide. Evidence governs.  
**Does not claim:** Staging pentest PASS · evidence-based Production GO · credential rotation DONE  

---

## 1. Mission outcomes

| # | Deliverable | Path | Disposition |
|---|-------------|------|-------------|
| 1 | Staging SSRF pentest checklist refreshed (actionable; HG-05 linked) | [../runbooks/staging-ssrf-pentest.md](../runbooks/staging-ssrf-pentest.md) | **Partial** (doc Fixed; execute **Human-Gate**) |
| 2 | Credential rotation instructions (JWT/DB/S3/OAuth; no secrets) | [CREDENTIAL-ROTATION-INSTRUCTIONS.md](./CREDENTIAL-ROTATION-INSTRUCTIONS.md) | **Fixed (doc)**; field rotate **Human-Gate** (HG-06 / RELEASE-BACKLOG #10) |
| 3 | Narrow local SSRF unit regression | `tests/unit/test_webhooks.py::TestWebhookSSRF` | **Fixed** (targeted green) — see §3 |
| 4 | Local KG e2e / staging KG probe | e2e + staging | **not validated** / staging **Human-Gate** (HG-05) |

---

## 2. Human gates (unchanged — not agent-closed)

| Gate | Topic | Link | Agent action |
|------|-------|------|--------------|
| **HG-05** | Staging SSRF / KG pentest execute | [HUMAN-GATE-CARD.md](./HUMAN-GATE-CARD.md#gate-hg-05--staging-ssrf--kg-pentest) | Checklist ready; **no PASS claim** |
| **HG-06** | Credential rotation field | [HUMAN-GATE-CARD.md](./HUMAN-GATE-CARD.md#gate-hg-06--credential-rotation) | Instructions published; **no live rotate** |

Prerequisite for HG-05: HG-01 staging host.

---

## 3. Targeted tests (low-load)

| Item | Command | Result | Validation label |
|------|---------|--------|------------------|
| SSRF unit class | `docker compose exec -T backend python -m pytest tests/unit/test_webhooks.py::TestWebhookSSRF -q --tb=line` (cwd `salesos/`) | **11 passed**, 1 warning (passlib/crypt deprecation), ~15.5s | **build validated** (narrow path) |
| Contract SSRF HTTP | `tests/contract/test_webhook_ssrf.py` | **not run** this wave (narrow unit path preferred) | **not validated** |
| KG e2e | `tests/e2e/test_knowledge_graph.py` | **not run** (heavier e2e / seed) | **not validated** |
| Staging pentest §4 table | Live `STAGING_HOST` probes | **not executed** (no agent staging PASS) | **not validated** / **Human-Gate** |

**Host note:** Windows host has no project venv `pytest`; execution used healthy local Docker `backend` (pytest via `python -m pytest`). No package install. No full suite.

---

## 4. Program board suggested updates (Director)

Stream D does not own `PROGRAM-BOARD.md`; recommend Director apply:

| ID | Suggested status | Notes |
|----|------------------|-------|
| CP-D-01 | Partial → doc ready | Execute remains Human-Gate |
| CP-D-02 | Open → Partial/Fixed (unit) | Unit SSRF green; KG still open |
| CP-D-03 | Open → Fixed (doc) | CREDENTIAL-ROTATION-INSTRUCTIONS.md |
| CP-REL-05 | Human-Gate | Unchanged |
| CP-REL-10 | Human-Gate | Unchanged |

---

## 5. Files touched this stream

| Path | Action |
|------|--------|
| `docs/audit/ga-engineering-audit/runbooks/staging-ssrf-pentest.md` | Refreshed — HG-05, operator steps, honest PASS rule |
| `docs/audit/ga-engineering-audit/completion/CREDENTIAL-ROTATION-INSTRUCTIONS.md` | **Created** |
| `docs/audit/ga-engineering-audit/completion/STREAM-D-M1.md` | **Created** (this file) |

**Not touched:** auth/CSRF/RBAC middleware · production secrets · SIGN_HERE · soak claims  

---

## 6. Residual honesty

- Staging JWT/SECRET isolation work (2026-08-07) ≠ full Item #10 closure — Postgres/Neo4j/OAuth/S3 field steps remain human ([SECURITY-SECRETS.md](../enterprise-audit-board/history/EAB-2026-08-06-003/SECURITY-SECRETS.md)).  
- Local unit green ≠ staging pentest PASS.  
- Human-declared GO (SIGN_HERE) ≠ evidence-based Production GO.

---

## 7. Exit criteria (M1 Stream D)

- [x] Pentest checklist actionable + HG-05 linked  
- [x] Credential rotation instructions published (no secrets)  
- [x] Narrow SSRF unit path run with recorded outcome  
- [ ] Staging pentest PASS — **Human-Gate**  
- [ ] Credential rotation field DONE — **Human-Gate**  

---

*Stream D M1 — 2026-08-08 — validation: SSRF unit build validated; staging/rotation not validated*
