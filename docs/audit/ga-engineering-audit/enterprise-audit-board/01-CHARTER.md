# 01 — Charter | الميثاق

**Pack:** Enterprise Audit Board v2.1  
**Role:** Purpose, scope, non-claims, authority  
**Status:** Framework — not an executed run

---

## 1. Purpose

Provide a durable institutional charter for **full-root** enterprise audits of SalesOS under AQLIYA so that:

1. Vision, product bible, capabilities, ADRs, implementation, APIs, UI, tests, runtime, and monitoring stay **traceable**.  
2. Architectural drift is **measured**, not only anecdotally found.  
3. CTO **cost of change** is explicit (engineering economics).  
4. **AI governance** is scored separately from Security, with honesty gates.  
5. Every future run reuses this pack — methodology is not reinvented.

**Core principle:** AI assists. Humans decide. Evidence governs.

---

## 2. Scope

| In scope | Out of scope (unless explicitly added to a run) |
|----------|--------------------------------------------------|
| SalesOS under `salesos/` | Inventing AuditOS / DecisionOS / LocalContentOS GA |
| Docs, ADRs, DEC series, SES, Product Bible as they relate to SalesOS | Marketing decks as evidence of readiness |
| Code, schema (Alembic), compose, runtime paths | Production cutover / secret rotation as “audit evidence” without approval |
| Fitness proposals + drift metrics | Fabricated axis scores or Production GO |
| AI surfaces under [AI_HONESTY.md](../AI_HONESTY.md) | Claiming FE Decision package or copilot as live GA AI |

**Platform intent:** AQLIYA — Private Governed Institutional Intelligence.  
**Shipped code focus:** SalesOS. Do not equate SalesOS GA work with multi-product AQLIYA GA.

---

## 3. Two boards, two jobs

| Board | Artifact | Job |
|-------|----------|-----|
| **v1 Principal** | [PRINCIPAL-AUDIT-BOARD-2026-08-06.md](../PRINCIPAL-AUDIT-BOARD-2026-08-06.md) | Current-state **Production GA GO/NO-GO** engineering scorecard |
| **v2 / v2.1 Enterprise** | This pack | Full-root methodology: vision → … → monitoring across **43** axes |

v1 remains authoritative for the **2026-08-06** pre-launch engineering verdict (**Production GA NO-GO**). v2.1 does **not** supersede v1 scores until a human-approved **run** produces a dated findings pack.

---

## 4. Non-claims (binding)

This charter and pack:

- Do **not** claim axes were executed.  
- Do **not** invent 0–100 scores or dimension rollups.  
- Do **not** claim Production GO, browser pass, or green full suites.  
- Do **not** weaken auth, CSRF, RBAC, tenant isolation, audit logging, or evidence gates “for demos.”  
- Do **not** market stubs as production AI (`feature_ai_copilot` default **False**; FE `@salesos` decision package is a **STUB**).

Standing classification (until evidence upgrades it): **production no-go** — see [GA_STATUS.md](../GA_STATUS.md), [00-EXECUTIVE-SUMMARY.md](../00-EXECUTIVE-SUMMARY.md).

---

## 5. Authority chain

1. **Executable evidence** (commands, dated run appendices, signed gates)  
2. **ga-engineering-audit** folder (this pack + Principal Board + wave progress)  
3. [`AGENTS.md`](../../../../AGENTS.md) — agent law, low-load, product boundaries  
4. [`docs/PROJECT_BIBLE.md`](../../../PROJECT_BIBLE.md) — engineering bible; **audit wins** on GO/NO-GO conflicts  

Superseded GO artifacts (`docs/vnext/reports/GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md`, etc.) must not be cited as authority.

---

## 6. Relation to AQLIYA / SalesOS

| Concept | Honest stance |
|---------|----------------|
| AQLIYA | Platform intent — Private Governed Institutional Intelligence |
| SalesOS | First operational product; primary codebase |
| Other OS products | Vision / separate products — not shipped GA trees here |
| AI | Assistive only until evidence + flags + honesty gates say otherwise |

---

## 7. GO / NO-GO honesty

- Default for any unexecuted or incomplete run: **production no-go**.  
- **pilot-ready with conditions** requires listed P0s closed with evidence.  
- **Production GO** requires executable evidence per [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md) and synthesis rules in [07-SCORING-MODEL.md](./07-SCORING-MODEL.md).  
- Docs-only upgrades of labels are **forbidden**.

---

## 8. Next human action

**Approve a v2.1 board run:** scope, workstreams, evidence budget, any heavy-command exceptions — then instantiate [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md).

---

*Charter — Enterprise Audit Board v2.1*
