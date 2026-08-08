# Soak Progress Snapshot — 2026-08-08 (Stream A)

**Classification:** **IN PROGRESS** — not complete  
**`soak_complete_claim`:** **false**  
**Do not cite:** 576/576, 48–72h PASS, evidence-based Production GO

**Harness card:** [SOAK-HARNESS-INSTRUCTIONS.md](./SOAK-HARNESS-INSTRUCTIONS.md)  
**This refresh:** WAVE-20260808-5 — [evidence/wave-20260808-5/_soak-stats.txt](./evidence/wave-20260808-5/_soak-stats.txt)

---

## Live harness (machine observed WAVE-5)

| Field | Value |
|-------|--------|
| Snapshot UTC | **2026-08-08T10:34:00Z** (recount after i242) |
| PID (this host) | **16044** (`python … wave11-soak-gate.py --loop … --duration-hours 72`) — **alive** |
| API | `https://salesos-staging.up.railway.app` |
| FE | `https://sales-os-jet.vercel.app` |
| Evidence dir | `enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-staging/` |
| Loop JSON count | **242** |
| `gate_pass` iters | **242** / fail **0** |
| First / last | `2026-08-07T14:10:06Z` i1 → `2026-08-08T10:30:23Z` i242 |
| Elapsed from start | **~20.3 h** of **72 h** target |
| Remaining (approx) | **~51.7 h** |
| Expected iters @ 5 min / 72h | **864** (not 576 — 576 ≈ 48h @ 5 min) |

**Honesty:** Mid-window health-loop evidence only (~20.3h / 72h). K2–K6 remain OPEN until wall-clock ≥48–72h + TL review + claim flip by human. **Do not start a second soak loop** while PID 16044 writes this evidence dir.

---

## Prior snapshots (superseded for live counts)

| Wave | Snapshot UTC | Loops | Elapsed |
|------|--------------|------:|--------:|
| W3 | 2026-08-07T23:12:10Z | 108 | ~9.0 h |
| W4 | 2026-08-08T10:16:00Z | 239 | ~20.1 h |
| W5 (this) | 2026-08-08T10:34:00Z | 242 | ~20.3 h |

---

## Local Docker readiness (WAVE-2 — not staging soak)

| Field | Value |
|-------|--------|
| Command | `wave11-soak-gate.py` oneshot `--api http://localhost:8000` `--skip-alembic` |
| Exit | **0** GATE PASS (readiness only) |
| Evidence | `completion/evidence/wave-20260808-2/local-gate/gate-2026-08-07T230317Z.json` |
| Notes | Flags check UNVERIFIED (docker exec timeout); alembic SKIP |

Local GATE PASS ≠ cloud soak complete.

---

## Restart / status helper

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -StatusOnly
# Only if no live writer: -Start -DurationHours 72 -FailSoft
```

---

## Human actions still required

See [HUMAN-GATE-CARD.md](./HUMAN-GATE-CARD.md) **Do these 3 next** (keep harness → K2–K6 review → DR CLOSE or cred rotation).

**Validation:** **light validated** (process + loop JSON inventory). **production no-go** residual for soak claim.
