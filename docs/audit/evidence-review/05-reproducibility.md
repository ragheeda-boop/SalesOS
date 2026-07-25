# Reproducibility Assessment

**Audit date:** 2026-07-22  
**Scale:** YES = another engineer can re-run from repo + documented command and obtain comparable artifacts  
**PARTIAL** = script/config exists but env secrets, local Docker state, or missing logs block clean replay  
**NO** = claim has no command/artifact trail

---

## By wave

| Wave | Reproducibility | Basis |
|------|-----------------|-------|
| 0 FE lint/tsc/build | **NO** | No saved logs; would require approved full FE toolchain re-run |
| 1 Alembic | **PARTIAL** | Migrations + `check_alembic_head.py` reproducible; original upgrade stdout missing |
| 2 SEC code | **PARTIAL** | Source + unit tests in tree; no pytest transcript |
| 2 Load probes | **YES** | `evidence/wave2-load/` + `probe-wave2-load.ps1` (or sibling script) present |
| 3 Unit suite | **NO** | No JUnit/log; quarantine empty; count claims unreproducible from evidence |
| 4 FE image | **NO** | `fe-build.log` missing; compose build not archived |
| 5 Auth contracts | **NO** | Code-only; no probe pack |
| 6 AI honesty | **PARTIAL** | Config/stub reproducible by reading source; live 403 needs runtime |
| 7 Docs | **YES** | Files either present or not |
| 8 Observability | **PARTIAL** | Compose config YES; live scrape NO evidence |
| 9 Secrets | **PARTIAL** | Tree/CI YAML YES; scanner run NO |
| 10 Neo4j/WAL | **PARTIAL** | JSON exists; dump binaries on Docker volumes not in git |
| 10 pg_dump drill | **NO** | No machine evidence to replay from |
| 11 Soak gate/4h | **YES** | Script + loop-summary + loop JSON |
| 11 Soak 48h | **PARTIAL** | Script yes; run incomplete; host/PID dependent |
| 12 Gates | **PARTIAL** | Script exists; cited log folder missing |
| 12 Staging cloud | **YES** (as BLOCKED) | Probe JSON + re-probe steps |
| 12 Virtual staging | **PARTIAL** | Tabletop JSON + compose project; ports local-only |
| 13 Auth demo | **PARTIAL** | JSON + seed/smoke scripts; credentials env-only |
| 13 UI smoke | **NO** (as proven) | Spec exists; durable report under evidence missing/unreadable |
| 13 Full crawl | **YES** | `full-ui-crawl.ps1` + spec + report JSON |
| 14 Signatures | **N/A** | Human process; not engineer-reproducible as GO |

---

## Commands that are reproducible today (with local stack)

```powershell
# Wave 11 oneshot gate (requires stack up)
python -u salesos/scripts/wave11-soak-gate.py --api http://localhost:8000 --fe http://localhost:3000 --compose-dir salesos

# Wave 13 crawl (requires credentials + stack)
cd salesos
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<env only>'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\full-ui-crawl.ps1
```

Re-running these proves **current** state only. It does not backfill missing Wave 0–5 logs.

---

## Commands that are not evidenced as having been run successfully

| Command family | Why NO |
|----------------|--------|
| `npm run lint` / `tsc` / `build` (post-fix) | No exit-0 artifact |
| Full `pytest tests/unit` green suite | No JUnit/log |
| `docker compose build frontend` (Wave 4 cited) | Missing `fe-build.log` |
| Observability scrape matrix | Admitted not run |
| Cloud `deploy-staging` | Probe BLOCKED |
| Production alembic upgrade | Explicitly blocked |
| k6 / load soak | Not run |

---

## Reproducibility blockers

1. **Secrets** — smoke/crawl need `SMOKE_*` / vault credentials not in evidence.  
2. **Local Docker volume state** — Neo4j dumps, postgres dumps not in git.  
3. **Low-load protocol** — auditors must not silently re-run heavy suites without approval.  
4. **Host sleep / PID** — 48h soak not wall-clock complete; restart resets window.  
5. **Remote GH Environment** — staging secrets/environments count 0; cannot reproduce cloud tabletop.

---

## Verdict on reproducibility of “Production Ready”

**NO.**

Production readiness is not a reproducible green path in this repository today. Local light scripts are reproducible; production gates are not closed.
