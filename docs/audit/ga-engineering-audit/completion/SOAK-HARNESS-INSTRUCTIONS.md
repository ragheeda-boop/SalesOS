# Staging Soak Harness — Copy-Paste Commands

**Date:** 2026-08-08  
**Stream:** A (OPS Launch) — M2 prove prep  
**Principle:** Evidence only. Humans decide claim flip. Agents do not invent PASS.

**Live window (observed):** started `2026-08-07T14:10:06Z` → target end `2026-08-10T14:10:06Z` (72h)  
**`soak_complete_claim`:** **false** until K1–K6 + TL review

---

## 0. Do these first (human)

1. Confirm only **one** writer to `ops01-staging/` (StatusOnly below).  
2. Do **not** start a second `--loop` while PID is alive.  
3. After ≥48–72h wall-clock: review [SOAK-GATE-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) K2–K6; only then flip claim.

---

## 1. Status (safe anytime)

```powershell
cd C:\Users\raghe\Documents\Muhide
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -StatusOnly
```

Expected fields: `loop_json_count`, `last_iteration`, `LIVE_HARNESS` PID (or none).

---

## 2. Live harness already running (do not duplicate)

If StatusOnly shows a `wave11-soak-gate` process with `--duration-hours`:

- Leave it running.  
- Deposit continues under:

```text
docs\audit\ga-engineering-audit\enterprise-audit-board\history\EAB-2026-08-06-003\evidence\ops01-staging\
```

- Optional inventory refresh (agent-safe):

```powershell
cd C:\Users\raghe\Documents\Muhide
$ops = "docs\audit\ga-engineering-audit\enterprise-audit-board\history\EAB-2026-08-06-003\evidence\ops01-staging"
(Get-ChildItem $ops -Filter "loop-*.json").Count
Get-ChildItem $ops -Filter "loop-*.json" | Sort-Object Name | Select-Object -Last 1 | ForEach-Object { $_.Name; Get-Content $_.FullName -Raw | ConvertFrom-Json | Select-Object iteration, timestamp, gate_pass }
```

---

## 3. Start / restart 72h staging loop (ONLY if no live writer)

```powershell
cd C:\Users\raghe\Documents\Muhide
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 `
  -Start -DurationHours 72 -FailSoft `
  -ApiUrl "https://salesos-staging.up.railway.app" `
  -FrontendUrl "https://sales-os-jet.vercel.app"
```

Equivalent direct Python:

```powershell
cd C:\Users\raghe\Documents\Muhide
$env:PYTHONUNBUFFERED = "1"
$ev = "docs\audit\ga-engineering-audit\enterprise-audit-board\history\EAB-2026-08-06-003\evidence\ops01-staging"
New-Item -ItemType Directory -Force -Path $ev | Out-Null
python -u salesos\scripts\wave11-soak-gate.py `
  --loop --interval 300 --duration-hours 72 `
  --api https://salesos-staging.up.railway.app `
  --fe https://sales-os-jet.vercel.app `
  --skip-alembic --skip-flags --fail-soft `
  --evidence-dir $ev
```

---

## 4. Local readiness gate only (NOT cloud soak)

```powershell
cd C:\Users\raghe\Documents\Muhide
$out = "docs\audit\ga-engineering-audit\completion\evidence\wave-20260808-3\local-gate"
New-Item -ItemType Directory -Force -Path $out | Out-Null
python -u salesos\scripts\wave11-soak-gate.py `
  --api http://localhost:8000 `
  --fe http://localhost:3000 `
  --compose-dir salesos `
  --skip-alembic `
  --evidence-dir $out
```

Local GATE PASS ≠ 48–72h soak complete.

---

## 5. After window — human claim path

1. Confirm elapsed ≥48h (prefer 72h) from first `loop-*.json` timestamp.  
2. Triage any `gate_pass=false` iters.  
3. Complete K2–K6 in SOAK-GATE-CHECKLIST.  
4. Human TL review + Project Owner flips `soak_complete_claim` in the authoritative claim doc.  
5. Agents **must not** flip the claim.

---

## Snapshot (this wave inventory)

See [SOAK-PROGRESS-SNAPSHOT-2026-08-08.md](./SOAK-PROGRESS-SNAPSHOT-2026-08-08.md) and `evidence/wave-20260808-3/soak-status/_soak-stats.txt`.

**Validation:** harness tooling **light validated**; soak complete **not validated** / claim **false**.

---

*Copy-paste harness card — Completion Program — no forged PASS*
