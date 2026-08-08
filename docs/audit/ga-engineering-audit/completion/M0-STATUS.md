# M0 Status — Stabilize

**Milestone:** M0  
**Date:** 2026-08-08  
**Program:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Board:** [PROGRAM-BOARD.md](./PROGRAM-BOARD.md)

---

## Objective

Unblock targeted pytest import path; align CRITICAL governance contradiction **labels** to evidence without inventing CLOSE; lock stream ownership.

---

## Outcomes

| Stream | Action | Result | Validation |
|--------|--------|--------|------------|
| **C** | Fix `main.py` FastAPI dual-path `@app.get("/api/v1/version", "/version", …)` → two decorators | Code fixed + import verified | **light validated** — Docker `from app.main import app` → `IMPORT_OK FastAPI` (see [STREAM-C-M1.md](./STREAM-C-M1.md)) |
| **F** | Align DR cutover gate language: drill facts vs CLOSED; RC-P0-01 map | In progress → see WAVE + AUTHORITATIVE addendum | **light validated** (docs) |
| **Director** | COMPLETION-PROGRAM + ownership locks + PROGRAM-BOARD + this file | Done | n/a |

---

## Boot regress detail (C)

**Symptom (GA-UPDATES-VERIFICATION-2026-08-08):**  
`TypeError: FastAPI.get() takes 2 positional arguments but 3 were given` at `salesos/backend/app/main.py:416`.

**Root cause:** Two path strings passed as positional args to `@app.get`.

**Fix:** Stacked decorators:

```python
@app.get("/api/v1/version", response_model=VersionResponse)
@app.get("/version", response_model=VersionResponse)
```

**File:** `salesos/backend/app/main.py`

---

## Governance (F) — label policy (no invented evidence)

| Claim class | Correct label |
|-------------|---------------|
| Offsite/WAL/PITR **drill JSON** | Evidence **DONE\*** (machine) — cite EAB-003 evidence paths |
| Cutover gate **CLOSED?** | Still **OPEN / Human-Gate** until human CLOSE on DR checklist |
| SIGN_HERE Decision=GO | **HUMAN-GO-INK** / human-declared GO |
| Soak 48–72h | **OPEN** (OPS01-04) |
| Evidence-based Production GO | **NOT claimed** |

RC-P0-01 resolution path: both sides true under different roles — facts vs gate CLOSED — see [GOVERNANCE-LABEL-ALIGNMENT.md](./GOVERNANCE-LABEL-ALIGNMENT.md).

---

## Exit criteria M0

- [x] Living program + locks published  
- [x] Boot TypeError code fix landed  
- [x] Targeted import / unit smoke (Stream C verify) — Docker import PASS 2026-08-08; full pytest not run  
- [x] Governance label alignment doc started  
- [x] Board seeded  

**Disposition:** M0 **Partial → continue into M1 immediately** (per order).

---

*M0 — Completion Program — 2026-08-08 — no commit*
