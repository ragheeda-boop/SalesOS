# 04 — Evidence Standard | معيار الأدلة

**Pack:** Enterprise Audit Board v2.1  
**Role:** What counts as evidence; validation labels; forbidden claims  
**Status:** Binding for every run

---

## 1. Validation labels

Reuse AQLIYA labels from [`AGENTS.md`](../../../../AGENTS.md):

| Label | Meaning |
|-------|---------|
| **not validated** | Not run / no evidence |
| **light validated** | Spot checks only (Grep/Read/static explore) |
| **build validated** | Install/lint/typecheck/build/test commands run with **recorded** outcome |
| **pilot-ready with conditions** | Narrow use after listed P0s closed with evidence |
| **production no-go** | Must not ship GA |

Optional run-local labels (must not inflate the five above):

| Label | Meaning |
|-------|---------|
| **N/A** | Axis not applicable to approved scope (justify) |
| **deferred** | Explicitly out of this run’s evidence budget |

---

## 2. What counts as evidence

| Acceptable | Not acceptable alone |
|------------|----------------------|
| Dated command output in run appendix | Undated “we usually pass” |
| File paths + line-referenced findings | Marketing copy / Notion vibe |
| Explore-agent IDs + summarized artifacts | Screenshots without context |
| Prior wave PROGRESS / APPENDIX files **cited with date** | Superseded GO docs as SoT |
| Fitness/drift metric tables with method | Invented scores |
| Signed or explicitly UNSIGNED gate blocks | Implied signature |

**Executable evidence** beats narrative. Audit wins over Product Bible maturity for GO/NO-GO.

---

## 3. Label upgrade rules

- Docs-only → cannot upgrade past **not validated** / narrative finding.  
- Static explore → at most **light validated**.  
- Approved narrow build/test → may reach **build validated** for that path only.  
- Full suite / soak / browser → only with explicit approval + recorded outcome.  
- Never upgrade Security or AI Governance on “intent” without runtime/config evidence.

---

## 4. Forbidden claims

Without recorded evidence in the run pack, forbid:

- Production GO / “ready for GA”  
- Browser pass / full UI crawl pass  
- Green full npm / pytest suites  
- “AI-native GA”, “98% AI PASS”, autonomous agents in production  
- Equating SalesOS GA with AQLIYA multi-product GA  
- Presenting FE Decision **STUB** or gated copilot as live production AI  
- Claiming axes 40–43 “passed” without matrices/metrics/scorecards  

AI claims must respect [AI_HONESTY.md](../AI_HONESTY.md): `feature_ai_copilot` default **False**.

---

## 5. Low-load interaction

Heavy commands (full build/lint/test, installs, prod migrate) require **explicit user approval**. Absence of approval → leave related axes **not validated** or **light validated**; do not invent **build validated**.

---

## 6. Evidence appendix (required in every run)

1. Commands run (or “none — read-only”)  
2. Agent / workstream IDs  
3. What was **not** run and why  
4. Pointers to external evidence (wave progress files)  
5. Any low-load exceptions granted  

---

*Evidence Standard — Enterprise Audit Board v2.1*
