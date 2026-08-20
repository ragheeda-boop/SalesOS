# SalesOS — Independent Live Verification of A-09 and OPS-01

**Verification window:** 2026-08-20T08:45Z → 2026-08-20T09:00Z
**Mode:** Read-only. No source changes, no infra changes, no restarts, no redeploys, no data mutation.
**Verifier evidence sources used:** live Chrome browser probes (staging API, production API, production frontend), Railway control-plane reads, Vercel control-plane reads, repository/working-tree reads on the operator machine.
**Repo working copy:** `C:\Users\raghe\Documents\Muhide`, branch `master`, HEAD `b06b14e`.

---

## 1. Executive Summary

**Final decision: NO-GO.**

This is not a "documentation not yet reconciled" outcome. Four independent, current, machine-verifiable failures were found during this verification:

1. **The production frontend cannot build.** Every production Vercel build since 2026-08-13T00:19Z has failed with `Module not found: Can't resolve '@/lib/company360Signals'`. The file `salesos/frontend/src/lib/company360Signals.ts` exists **only as an untracked file on the developer's local disk** — it was never committed. Production is serving a frontend from commit `110b0c8b`, six commits behind the backend.
2. **Staging is not a pre-production gate.** Staging and production deploy from the same repo, the same branch (`master`), with `watchPatterns: ["**"]`, and their last deployments started **within 1 second of each other** (staging 00:41:31.06Z, production 00:41:31.70Z on 2026-08-13). A build can never soak in staging before production receives it.
3. **Neo4j has no persistent volume in either environment.** `volumeMounts` is absent from the `neo4j-prod` service config in both the `production` and `staging` environments. There is no storage to back up, so OPS01-06 cannot be satisfied and the graph tier's effective RPO is total loss.
4. **No soak exists for the deployed build.** The last documented soak (2026-08-07→08-10, 72h) recorded 854 iterations / 82 failures / **9.6% fail rate** including a ~6h46m staging database outage, and `soak_complete_claim` was correctly left `false`. Both environments were then redeployed on 2026-08-13, resetting the clock. Current uptime is ~7.6 days but with **essentially zero traffic** (staging avg network RX ≈ 4.4e-9 GB/sample over 168h) — that is idle uptime, not a soak.

Additionally, the go-live signature record (OPS01-05) cannot be accepted as a valid approval: it is internally self-contradicting, both roles are signed by the same individual, it is dated 2026-08-08 (five days **before** the currently deployed commit), it names no commit or version, and it was introduced inside a 493-file / 64,023-line bulk documentation commit.

The DR primitives (offsite backup, WAL archive, PITR) have credible historical drill evidence, but all of it is dated 2026-08-06/07 — 13–14 days stale — and every evidence JSON carries `"signed_off_by": ""`. Per the evidence standard for this exercise, historical drills cannot be converted into a current PASS, and no browser-accessible backup console, WAL archiver view, or restore-drill result exists to re-verify them today. Those rows are **BLOCKED**, not PASS and not FAIL.

---

## 2. Expected State vs Actual State

| Dimension | Expected (per repo documentation) | Actual (verified 2026-08-20) | Verdict |
|---|---|---|---|
| Approved baseline commit | `4750038c` (`STAGING-vs-PRODUCTION-DIFF.md`, 2026-08-07) | Backend both envs `b06b14e`; frontend `110b0c8b` | **Baseline superseded, never re-approved** |
| Staging = pre-prod gate | Staging soaks before prod | Same branch, same trigger, deployed 0.64s apart | **FAIL** |
| Frontend | One Vercel app shared by both envs | Confirmed — no staging frontend exists | **Parity untestable** |
| Neo4j durability | "connected" in both envs; volume = known P1 | Still **no volume** in either env | **FAIL** |
| Soak requirement | ≥48h, prefer 72h, `soak_complete_claim: true` | Last soak 9.6% fail, claim `false`; no soak on current build | **FAIL** |
| RPO / RTO | RPO < 1h, RTO < 4h (`DR_RUNBOOK.md` §1) | Targets defined; no current evidence; graph tier unrecoverable | **FAIL / BLOCKED** |
| Go-live ink | CTO + Tech Lead | Same person both roles, pre-dates deployed commit | **FAIL** |

Canonical environment URLs identified from live control-plane data (not from documentation):

- Production API — `https://salesos-production-96c0.up.railway.app` (Railway project `responsible-comfort`, env `production`, service `SalesOS`)
- Staging API — `https://salesos-staging.up.railway.app` (same project, env `staging`, same service)
- Frontend — `https://sales-os-jet.vercel.app` (Vercel project `sales-os`, production alias)

---

## 3. A-09 — Staging Parity Verification

### A-09.1 Application Version

```
Test ID:      A-09.1
Requirement:  Staging and production run the approved baseline
Environment:  staging + production + frontend
Expected:     Both at approved baseline 4750038c; frontend matching
Actual:       Backend staging  = b06b14e (deploy aede6e04, 2026-08-13T00:41:31.06Z, SUCCESS)
              Backend prod     = b06b14e (deploy 1fd1cc7a, 2026-08-13T00:41:31.70Z, SUCCESS)
              celery-beat      = b06b14e in BOTH envs
              celery-worker    = b06b14e in production
              celery-worker    = 46b221ad in STAGING (2026-08-12T20:43:27Z) — BEHIND
              Frontend (prod)  = 110b0c8b (dpl_2mESVRGdg..., READY, 2026-08-13T00:05:33Z)
Evidence:     /health on both hosts returns version "5.1.0-rc1";
              Railway list-deployments per service/environment;
              Vercel get_deployment("sales-os-jet.vercel.app")
Timestamp:    2026-08-20T08:47Z – 08:55Z
Result:       FAIL
```

Three distinct version defects:

- **Backend ≠ frontend.** Backend `b06b14e`, frontend `110b0c8b` — six commits of drift, in production, right now.
- **Staging worker ≠ staging app.** The staging `celery-worker` is pinned at `46b221ad` from 2026-08-12T20:43Z, four hours and several commits behind the staging API it serves. Production's worker is correctly at `b06b14e`. Staging is therefore not even internally consistent, let alone a mirror of production.
- **Neither environment runs the approved baseline** `4750038c`. The baseline was superseded by ~30 commits with no re-approval record.

### A-09.2 API Contract Parity

```
Test ID:      A-09.2
Requirement:  Staging and production expose an identical API surface
Environment:  staging + production
Expected:     Byte-identical /openapi.json
Actual:       Both: HTTP 200, 904,710 chars, 602 paths
              16-chunk rolling checksums: 15/16 identical; chunk 16 differs
              32-sub-chunk narrowing of chunk 16: 31/32 identical; sub-chunk 19 differs
              Differing region (offset 881,748, len 1,767) is a single schema field:
                WorkloadSummary.generated_at default = "2026-08-13T00:42:50.648262" (prod)
              Endpoint behaviour identical in both envs:
                /health 200 · /metrics 200 · /docs 404 · /redoc 404 · /ready 404 · /healthz 404
                /api/v1/companies 401 · /api/v1/search 401 · /api/v1/activities 401
                /api/v1/tenants 404 · /api/v1/identity/me 404 · /api/v1/graph/health 404
Evidence:     In-page fetch + checksum of /openapi.json on each origin; status matrix per origin
Timestamp:    2026-08-20T08:49Z – 08:53Z
Result:       PASS
```

The only difference between the two documents is a `generated_at` default frozen at process import time. That is genuine parity.

Two side observations, both non-blocking for this gate:

- A `datetime.now()`-style value baked into a Pydantic schema default is a latent defect — the advertised default drifts further from reality the longer the process runs, and it makes the OpenAPI document non-reproducible.
- Production API responses carry `x-frame-options: DENY`, `x-content-type-options: nosniff`, `referrer-policy: strict-origin-when-cross-origin`, HSTS, and a restrictive CSP. No secrets were observed in any response header or body.

### A-09.3 Frontend Parity

```
Test ID:      A-09.3
Requirement:  Critical user flows behave identically in staging and production
Environment:  frontend
Expected:     A staging frontend and a production frontend to compare
Actual:       Only ONE frontend exists. FRONTEND_URL is https://sales-os-jet.vercel.app
              in BOTH Railway environments. Vercel project "frontend" (prj_o19B...) is
              live:false, target:null — not a staging frontend.
              Login/Dashboard/Company List/Company 360/Activity Intelligence/search/logout
              require credentials; none are available to this verification, and entering
              credentials is outside what I may do.
Evidence:     Vercel list_projects / get_project; Railway service config (FRONTEND_URL present
              in both envs); manual navigation to /login
Timestamp:    2026-08-20T08:51Z – 08:58Z
Result:       BLOCKED — NOT VERIFIABLE FROM AVAILABLE BROWSER ACCESS
              (structurally untestable: no staging frontend exists to compare against)
```

What *was* verifiable at the frontend, and it is serious:

```
Test ID:      A-09.3b
Requirement:  Production frontend deploys current code
Environment:  production frontend
Expected:     Latest master build serving
Actual:       Last SIX production-target Vercel builds = state ERROR:
                b06b14e, 8ed3608, b2c551a, 60a1532, ee5e4bb, 8296c60
              Last READY production build = 110b0c8b (2026-08-13T00:05:33Z) — currently aliased
              Build failure (dpl_GMFqj7qJ8FvYFtUkD5P8pHVKYLTJ, 2026-08-13T00:42:23Z):
                ./src/app/(dashboard)/companies/[id]/360/page.tsx
                Module not found: Can't resolve '@/lib/company360Signals'
                > Build failed because of webpack errors
              Root cause confirmed on the operator machine:
                git status → "?? salesos/frontend/src/lib/company360Signals.ts"
                (also "?? .../__tests__/company360Signals.test.ts")
              The module exists only as an UNTRACKED local file. It is not in the repository.
Evidence:     Vercel list_deployments + get_deployment_build_logs(errorsOnly);
              `git ls-files` / `git status --porcelain` on the working tree
Timestamp:    2026-08-20T08:55Z – 08:58Z
Result:       FAIL — BLOCKING
```

This single defect explains the version drift in A-09.1 and means production cannot ship a frontend fix today even if one were needed.

**Rendering anomaly (reported as an observation, not scored):** the production `/login` route returns complete server-rendered HTML (HTTP 200, 15,114 bytes, login form markup, `x-vercel-cache: HIT`), but in the live Chrome session the DOM ends up with no application nodes — `document.body.innerText.length === 0`, only extension-injected `<div>`s remain, and the tab title flickers to `SalesOS - Enterprise Company Intelligence Platform` before reverting to empty. No console errors were captured. Two Chrome extensions (Apollo, Monica) are active in this profile and inject into the page. I could not separate extension interference from a client-side crash, so I am not scoring this. **It needs a clean-profile re-test before go-live** — if it reproduces without extensions, it is a P0.

### A-09.4 Runtime Health

```
Test ID:      A-09.4
Requirement:  Both environments healthy across all dependency tiers
Environment:  staging + production
Expected:     /health 200, all subsystems connected
Actual:       Production /health:
                status=ok  version=5.1.0-rc1  database=connected  cache=connected
                graph=connected  kafka=in_memory  redis=connected  rate_limiter=active
                uptime_seconds=633788.19
              Staging /health:
                identical field set and values; uptime_seconds=633812.86
              Both uptimes reconcile to the 2026-08-13T00:42Z deployments.
              API routing: frontend proxies /api/v1/* same-origin through Vercel
                (server: Vercel, 401 {"detail":"Not authenticated"}) — no CORS dependency,
                no cross-environment leakage observed.
              Network requests on /login: 58 requests, all HTTP 200, no 4xx/5xx,
                no mixed content, no unexpected redirects, no exposed secrets.
Evidence:     Browser /health reads; in-page endpoint status matrix; read_network_requests
Timestamp:    2026-08-20T08:47Z – 08:56Z
Result:       PASS (health-endpoint level only)
```

Caveat stated plainly: `graph=connected` is true and simultaneously meaningless as a durability signal — see OPS01-06. A connected Neo4j with no volume is one redeploy away from being an empty Neo4j.

### A-09.5 Required Soak

```
Test ID:      A-09.5
Requirement:  ≥48h (prefer 72h) staging soak with soak_complete_claim true
Environment:  staging
Expected:     A completed, passing soak on the build under consideration
Actual:       Most recent soak: 2026-08-07T14:10:06Z → 2026-08-10T14:10:03Z
                854 iterations · 82 failures · 9.6% fail rate
                C1: contiguous ~6h46m staging DB outage (i583–i663), including
                    "password authentication failed for user salesos_app"
                soak_complete_claim: false  (correctly not flipped)
              Both environments then REDEPLOYED 2026-08-13T00:41Z → soak clock reset.
              No soak evidence exists for the deployed build b06b14e.
              Current uptime 7.6d, but Railway 168h metrics show the environment is IDLE:
                staging  CPU avg 0.0013 cores · NETWORK_RX avg 4.393e-9 GB/sample
                prod     CPU avg 0.0014 cores · NETWORK_RX avg 4.491e-9 GB/sample
Evidence:     SOAK-72H-FAILURE-TRIAGE-2026-08-12.md + evidence/ops01-staging/ (860 files);
              Railway list-deployments; Railway get-service-metrics (hoursBack 168)
Timestamp:    2026-08-20T08:53Z – 08:57Z
Result:       FAIL
```

Uptime without traffic is not a soak. An idle process proves the process starts; it proves nothing about connection-pool exhaustion, queue backpressure, credential rotation, memory growth under load, or the exact class of failure that took staging's database down for nearly seven hours on 2026-08-09.

---

## 4. OPS-01 — Disaster Recovery Verification

### OPS01-01 — Offsite Backup

```
Test ID:      OPS01-01
Requirement:  Production backups exist offsite, with retention and a proven restore
Expected:     A current successful backup with timestamp, destination, retention
Actual:       Configuration present TODAY: production Postgres service carries
                WAL_ARCHIVE_BUCKET / _ENDPOINT / _KEY / _REGION / _SECRET (values not read)
              Latest restore evidence is HISTORICAL, dated 2026-08-06:
                salesos_prod_20260806.dump · 20,167,454 bytes · pg_dump -Fc
                bucket salesos-backups-iwrweogrr (region sjc, endpoint t3.storageapi.dev)
                download SHA-256 match: true · pg_restore exit 0 in 29s
                96 tables · 141,221 companies · alembic d1a8c35e7f09 matched live
                retention: "bucket + operator schedule under review"
                "signed_off_by": ""
              No browser-accessible backup console, job history, or object listing exists.
              No successful backup after 2026-08-06 could be observed.
Evidence:     Railway get-service-config (Postgres, production);
              evidence/ops01-offsite/ops01-row1-offsite-restore.json
Timestamp:    2026-08-20T08:54Z
Result:       BLOCKED — latest verifiable backup artifact is 14 days old; no current job
              result observable; automated schedule + retention policy still unclosed
```

### OPS01-02 — WAL Archiving

```
Test ID:      OPS01-02
Requirement:  WAL archiving actually operating, not merely archive_mode=on
Expected:     Recent WAL archive activity with timestamps and zero failures
Actual:       Configuration present today (WAL_ARCHIVE_* vars on the prod Postgres service).
              Last operational proof is 2026-08-07:
                archive_mode=on · archived_count 1240 · failed_count 0
                last_archived_wal 000000010000000500000032
                destination s3://salesos-pitr-w-857q3fjjrr/pgbackrest/cluster-...
                pgBackRest 2.59.0 · retention 4 full / 14 diff (~4 weeks)
                "signed_off_by": ""
              pg_stat_archiver cannot be queried from the browser and I will not open a
              database tunnel during a read-only verification.
Evidence:     evidence/ops01-pitr/prod-live-wal-archive-reverify-2026-08-07.json;
              Railway get-service-config variableNames
Timestamp:    2026-08-20T08:54Z
Result:       BLOCKED — cannot verify operational WAL archival as of today
```

### OPS01-03 — PITR

```
Test ID:      OPS01-03
Requirement:  Point-in-time recovery operational (not merely pg_dump restore)
Expected:     Base backup + WAL continuity + a recent restore-to-timestamp drill
Actual:       Historical drill 2026-08-06 (ops01-row3-pitr-restore.json) with a real
              pgBackRest full backup: label 20260806-192926F, 385,691,087 bytes delta,
              LSN 0/5D000028 → 0/5D000158, error:false, archive range 5C → 61.
              DR_RUNBOOK records ~5–10 min measured PITR restore.
              Railway native volumeInstancePITRRestore is "Not Authorized".
              No isolated restore environment is available to me, and I will not run a
              destructive or write-path restore against production.
Evidence:     evidence/ops01-pitr/ops01-row3-pitr-restore.json; DR_RUNBOOK.md §1
Timestamp:    2026-08-20T08:54Z
Result:       BLOCKED — PITR cannot be safely demonstrated from the browser; last drill 14 days old
```

### OPS01-04 — Staging Soak

Same evidence as A-09.5. **FAIL.** Restating the distinction the brief asked for: the failure here is not "the soak is still running." It is that the last soak **failed on its own gate criteria** (9.6%, DB down 6h46m, `soak_complete_claim: false`), and the build it ran against no longer exists in either environment.

### OPS01-05 — Go-Live Signatures

```
Test ID:      OPS01-05
Requirement:  CTO and Tech Lead approval, dated, covering a specific version/commit,
              recorded after the readiness evidence
Expected:     Two independent human approvals naming the release
Actual:       docs/releases/v1.0.0-ga/signatures/SIGN_HERE.md contains:
                CTO      — SIGNED: GO — 2026-08-08 — رغيد المدني
                Tech Lead— SIGNED: GO — 2026-08-08 — رغيد المدني
              Defects in that record:
                (a) Same individual signs BOTH roles — no independent second approval.
                    The project's own DR checklist flags this as "dual-role P1".
                (b) No commit, build ID, or version is named anywhere in the signature block.
                (c) Dated 2026-08-08 — FIVE DAYS BEFORE the currently deployed commit
                    b06b14e (2026-08-13). The approval cannot cover what is deployed.
                (d) The SAME FILE still carries, unedited above the signatures:
                    "CTO Decision recorded 2026-08-06: NO-GO", "Tech Lead block remains
                    UNSIGNED", "Agents must not fill names, dates, or Decision=GO",
                    and nine open blockers including "48–72h soak NOT complete".
                (e) The companion index GO-LIVE-SIGNATURE-PACKET.md still reads
                    "Go-Live Signature Packet Index — UNSIGNED", with all five
                    preconditions unchecked.
                (f) git history: the signature was introduced in a single commit,
                    f64c2a6 (2026-08-08, Ragheed), which changed 493 files and added
                    64,023 lines of documentation. It is not a discrete, auditable
                    approval act.
Evidence:     SIGN_HERE.md (tail), GO-LIVE-SIGNATURE-PACKET.md, DR-GA-GAPS-CHECKLIST.md row 5,
              `git log`/`git show --stat` for f64c2a6
Timestamp:    2026-08-20T08:56Z
Result:       BLOCKED — no valid approval record for the deployed version
```

I am not asserting the signature was forged. I am asserting that as an approval artifact it fails every test the brief specified: it is not independent, it names no version, it pre-dates the artifact it would approve, and its own document contradicts it. A human must re-ink this against a named commit.

### OPS01-06 — Neo4j DR

```
Test ID:      OPS01-06
Requirement:  Neo4j backup policy, execution, retention, restore procedure
Expected:     A durable Neo4j with a backup/restore path
Actual:       Service "neo4j-prod" (2e84ce72-...), image neo4j:5-community.
              PRODUCTION env config: NO "volumeMounts" key present.
              STAGING env config:    NO "volumeMounts" key present.
              Compare: the Postgres service DOES report
                volumeMounts { 05512e31-... : "/var/lib/postgresql/data" }
              so the absence on Neo4j is a real difference, not a reporting gap.
              Only variables are NEO4J_AUTH and two listen-address settings — no backup
              configuration of any kind.
              Documented policy exists (DR_RUNBOOK §2.1: neo4j-admin dump, daily 04:00 UTC,
              7-day retention) but there is no storage for it to operate on and no
              execution evidence.
Evidence:     Railway get-service-config for neo4j-prod in both environments (read today)
Timestamp:    2026-08-20T08:53Z
Result:       FAIL
```

`/health` reporting `graph=connected` is exactly the trap the brief warned about. The graph tier is connected and simultaneously has zero recoverability: any redeploy, image auto-update, or host migration discards the entire graph. There is nothing to back up.

### OPS01-07 — Compose / Deployment Source of Truth

```
Test ID:      OPS01-07
Requirement:  Identify the authoritative deployment configuration; confirm staging and
              production use it; confirm deployed config matches the approved baseline
Expected:     One unambiguous source of truth, with staging gating production
Actual:       (a) STAGING IS NOT A GATE. Both environments:
                    source.repo   = ragheeda-boop/SalesOS
                    source.branch = master
                    watchPatterns = ["**"]
                  Last deploys started 0.64 SECONDS apart:
                    staging    aede6e04 @ 2026-08-13T00:41:31.064Z
                    production 1fd1cc7a @ 2026-08-13T00:41:31.696Z
                  Every one of the last 8 deployments in each env pairs 1:1 on the same
                  commit within ~1s. A build physically cannot soak in staging first.
              (b) TWO COMPETING CONFIG SOURCES. Railway reports configFile "railway.json"
                  yet service settings of:
                    build.dockerfilePath = "Dockerfile"
                    deploy.startCommand  = "python -m uvicorn app.main:app ..."
                  while the repo's railway.json at the deployed commit specifies:
                    dockerfilePath = "Dockerfile.railway"
                    startCommand   = the RAILWAY_SERVICE_NAME case-switch that selects
                                     celery worker vs beat vs uvicorn
                    restartPolicy  = ON_FAILURE, max 3 retries  (not reflected in the
                                     reported deploy config)
                  No file named "Dockerfile" exists at repo root or in salesos/
                  (`git ls-files` shows only Dockerfile.railway, Dockerfile.railway.celery,
                  salesos/backend/Dockerfile, salesos/frontend/Dockerfile, ...), yet builds
                  succeed — so railway.json evidently wins at build time and the stored
                  service settings are stale. Which layer is authoritative cannot be
                  confirmed from the browser.
              (c) Repo-root docker-compose.yml is documented as LEGACY/QUARANTINED
                  (COMPOSE-SOURCE-OF-TRUTH.md) but is still present at the repo root.
              (d) Undocumented environment differences found: staging SalesOS service is
                  missing GOOGLE_ENCRYPTION_KEY_PREVIOUS (present in production).
                  Environment variable VALUES could not be read (blocked), so value-level
                  parity — including database and secret isolation — is NOT verified.
Evidence:     Railway get-service-config (both envs, SalesOS + Postgres + neo4j-prod);
              Railway list-deployments (both envs, 8 each); repo railway.json;
              `git ls-files | grep Dockerfile`; docs/ops/COMPOSE-SOURCE-OF-TRUTH.md
Timestamp:    2026-08-20T08:50Z – 08:58Z
Result:       FAIL
```

**Item requiring human verification, flagged but not scored:** Railway reported the **same volume ID** `05512e31-396d-447c-b74a-a164792c02b6` mounted at `/var/lib/postgresql/data` for the Postgres service in **both** the `production` and `staging` environments. This may be an artifact of how the control-plane API renders service-level config across environments. If it is not, staging and production share a Postgres volume and staging is not isolated from production data. **I could not resolve this** — reading environment variable values was blocked. Given the blast radius, confirm this before any further staging activity.

### OPS01-08 — RPO / RTO

```
Test ID:      OPS01-08
Requirement:  Formally defined RPO/RTO, and evidence the DR posture actually meets them
Environment:  production
Expected:     Demonstrated compliance, not merely documented targets
Actual:       Targets ARE formally defined (DR_RUNBOOK.md §1):
                RPO < 1 hour · RTO < 4 hours · backup window 02:00–04:00 UTC
                DR failover < 30 min — explicitly "Not implemented (single-region)"
              Against those targets:
                Postgres RPO: plausibly minutes-class IF WAL archiving is healthy — but
                  health was last proven 2026-08-07 (OPS01-02 BLOCKED). Documented fallback
                  if the WAL path is unavailable is ~24h, which BREACHES RPO < 1h.
                Neo4j RPO:   TOTAL LOSS. No volume, no backup, nothing to restore.
                  No RPO target can be met for the graph tier. (OPS01-06)
                Postgres RTO: ~5–10 min measured — but in a 2026-08-06 drill, unrepeated.
                Neo4j RTO:   undefined; there is no restore procedure to time.
                Railway native volumeInstancePITRRestore: "Not Authorized".
              RPO acceptance signature: UNSIGNED (SIGN_HERE item 8; DR checklist row 8 OPEN).
Evidence:     DR_RUNBOOK.md §1–2.1; Railway neo4j-prod config (no volume);
              DR-GA-GAPS-CHECKLIST.md row 8; SIGN_HERE.md item 8
Timestamp:    2026-08-20T08:53Z – 08:56Z
Result:       FAIL — the Neo4j tier demonstrably cannot satisfy any RPO/RTO target;
              the Postgres tier is unproven as of today and formally unaccepted
```

---

## 5. Browser Security / Runtime Checks

| Check | Finding |
|---|---|
| Console errors | None captured on any probed page (see A-09.3 anomaly caveat) |
| Failed network requests | None — 58/58 requests on `/login` returned 200 |
| Unexpected 5xx | None observed |
| Authentication behaviour | Consistent: 401 `{"detail":"Not authenticated"}` on protected routes in **both** environments |
| Exposed secrets | None observed. No secret values are reproduced in this report. |
| Incorrect environment URLs | None at request level — the frontend proxies `/api/v1/*` same-origin via Vercel |
| Staging calling production APIs | Not observed |
| Production calling staging services | Not observed |
| CORS configuration | Not applicable — same-origin proxy. Direct cross-origin browser calls from the frontend origin to either Railway host are refused, which is correct given the proxy design. |
| Cookies / session | Not exercised — no authenticated session available |
| Mixed content | None |
| Unexpected redirects | None |
| **Additional finding** | Production **and** staging Postgres images carry an **armed HIGH-severity CVE remediation**: `CVE-2026-15741`, `armedAt: 2026-08-20T02:44:44Z`, current version 18.4, with automatic image updates scheduled (Sat 10:00–24:00, Sun 00:00–18:00). An unpatched HIGH CVE is live now, and an unattended auto-update of the production database is pending inside the next change window. |

---

## 6. Evidence Register

| # | Artifact | Source | Timestamp |
|---|---|---|---|
| E1 | `/health` production — `5.1.0-rc1`, all subsystems connected, uptime 633788.19s | Browser | 2026-08-20T08:47Z |
| E2 | `/health` staging — identical fields, uptime 633812.86s | Browser | 2026-08-20T08:47Z |
| E3 | `/openapi.json` both envs — 904,710 chars, 602 paths, 31/32 chunks identical | Browser fetch + checksum | 2026-08-20T08:49–08:53Z |
| E4 | OpenAPI delta isolated to `generated_at` default at offset 881,748 | Browser | 2026-08-20T08:52Z |
| E5 | Unauthenticated endpoint status matrix identical across envs | Browser | 2026-08-20T08:53Z |
| E6 | Railway deployments — staging `aede6e04` / prod `1fd1cc7a`, both `b06b14e`, 0.64s apart | Railway API | 2026-08-20T08:50Z |
| E7 | Staging `celery-worker` `f423f787` @ `46b221ad`, 2026-08-12T20:43:27Z | Railway API | 2026-08-20T08:54Z |
| E8 | Vercel: 6 consecutive production builds in state ERROR | Vercel API | 2026-08-20T08:55Z |
| E9 | Vercel build log — `Module not found: Can't resolve '@/lib/company360Signals'` | Vercel build logs | 2026-08-20T08:58Z |
| E10 | `git status --porcelain` — `?? salesos/frontend/src/lib/company360Signals.ts` (untracked) | Working tree | 2026-08-20T08:58Z |
| E11 | `sales-os-jet.vercel.app` → `dpl_2mESVRGdg...` @ `110b0c8b`, READY | Vercel API | 2026-08-20T08:55Z |
| E12 | `neo4j-prod` config, **both** envs — no `volumeMounts` | Railway API | 2026-08-20T08:53Z |
| E13 | Postgres config — `volumeMounts` present; `WAL_ARCHIVE_*` vars present; armed `CVE-2026-15741` | Railway API | 2026-08-20T08:53Z |
| E14 | 168h metrics — staging & prod CPU ≈0.0013 cores, NETWORK_RX ≈4.4e-9 GB/sample | Railway metrics | 2026-08-20T08:55Z |
| E15 | Soak triage — 854 iters / 82 fails / 9.6%; 6h46m DB outage; claim `false` | Repo (2026-08-12) | 2026-08-20T08:56Z |
| E16 | Offsite restore JSON — 2026-08-06, SHA match, `signed_off_by: ""` | Repo | 2026-08-20T08:55Z |
| E17 | WAL reverify JSON — 2026-08-07, archived 1240, failed 0, `signed_off_by: ""` | Repo | 2026-08-20T08:55Z |
| E18 | PITR drill JSON — 2026-08-06, pgBackRest `20260806-192926F`, error:false | Repo | 2026-08-20T08:55Z |
| E19 | `SIGN_HERE.md` — dual-role GO 2026-08-08 vs in-file NO-GO/UNSIGNED text | Repo | 2026-08-20T08:56Z |
| E20 | `git show --stat f64c2a6` — 493 files, 64,023 insertions | Working tree | 2026-08-20T08:57Z |
| E21 | `git ls-files` — no root `Dockerfile`; railway.json specifies `Dockerfile.railway` | Working tree | 2026-08-20T08:58Z |
| E22 | Frontend `/api/v1/companies` → 401 via `server: Vercel` proxy | Browser | 2026-08-20T08:57Z |

Rejected as evidence, per the brief: every "the previous audit passed" claim, every `DONE*` marker, and every drill JSON older than this verification window used on its own to justify a PASS.

---

## 7. Failed / Blocked Items

**FAIL (7)**

1. A-09.1 — Frontend six commits behind backend; staging worker behind staging app; neither env on the approved baseline.
2. A-09.3b — Production frontend build broken by an uncommitted module; six consecutive failed production builds.
3. A-09.5 / OPS01-04 — Last soak failed at 9.6%; no soak exists for the deployed build; current uptime is idle.
4. OPS01-06 — Neo4j has no persistent volume in either environment.
5. OPS01-07 — Staging and production deploy in lockstep from the same branch; staging is not a gate.
6. OPS01-07 — Deployment configuration has two competing sources with contradictory values.
7. OPS01-08 — RPO/RTO not demonstrable; graph tier structurally cannot meet any target.

**BLOCKED (5)**

1. A-09.3 — Frontend parity structurally untestable (no staging frontend) and authenticated flows unavailable (no credentials).
2. OPS01-01 — Offsite backup: latest artifact 14 days old; no current job result observable.
3. OPS01-02 — WAL archiving: last operational proof 2026-08-07; `pg_stat_archiver` not browser-reachable.
4. OPS01-03 — PITR: cannot be safely demonstrated; no isolated restore environment.
5. OPS01-05 — Go-live approvals: no valid record covering the deployed version.

**Requires human resolution before further staging work**

- Possible shared Postgres volume between staging and production (see OPS01-07 note).
- Armed HIGH CVE `CVE-2026-15741` on production Postgres with an unattended auto-update pending.
- Blank-render anomaly on production `/login` in a real browser session — needs a clean-profile re-test.

---

## 8. Discrepancies Against Previous Audit

Where current browser and control-plane evidence contradicts prior documentation, current evidence wins.

| # | Prior claim | Current evidence | Verdict |
|---|---|---|---|
| D1 | `STAGING-vs-PRODUCTION-DIFF` row 1: both envs at baseline `4750038c` | Both at `b06b14e`; frontend at `110b0c8b` | **Superseded** — baseline moved ~30 commits with no re-approval |
| D2 | `OPS01-ROW4-STATUS`: "Production Readiness ~96%", "Verification 100%" | Production frontend cannot build; no valid soak; Neo4j not durable | **Contradicted** |
| D3 | Row 26: staging `celery-worker` redeployed to match production | Staging worker is at `46b221ad`, behind its own app | **Regressed since 2026-08-07** |
| D4 | Row 14: Neo4j "connected" in both envs, treated as repaired | Connected, but **no volume in either env** — connected ≠ durable | **Materially incomplete** |
| D5 | Rows 18–19: WAL/offsite absent on staging, present on production | Both envs' Postgres services carry `WAL_ARCHIVE_*` vars; operation unverified in either | **Changed; unverified** |
| D6 | Row 15/16: "staging CI not yet exercised", staging as a distinct gate | Staging and prod deploy from the same branch 0.64s apart | **Contradicted** — staging was never a gate |
| D7 | `DR-GA-GAPS-CHECKLIST` row 7: Compose SoT "DOC FIXED" | Railway service settings still contradict repo `railway.json` | **Doc fixed, reality not** |
| D8 | `SIGN_HERE.md` header: "CTO: SIGNED GO; Tech Lead: SIGNED GO" | Same file's body: NO-GO, UNSIGNED, nine open blockers; packet index UNSIGNED | **Self-contradicting** |
| D9 | `GA_STATUS` #7: offsite + WAL + PITR **DONE 2026-08-06** | Drills real, but 14 days stale and unsigned — cannot be a current PASS | **Not current** |
| D10 | `DR-GA-GAPS-CHECKLIST` EAB-003 block: prod `archive_mode` "still off" | 2026-08-07 reverify shows `archive_mode=on`, archived 1240, failed 0 | **Prior claim was wrong** (in production's favour) |

D10 is worth stating explicitly: on that one point the pessimistic document was inaccurate and the evidence tree was right.

---

## 9. Final Go / No-Go Matrix

| Gate | Requirement | Result | Evidence | Blocking? |
|---|---|---|---|---|
| A-09 | Staging parity (version) | **FAIL** | E6, E7, E8, E11 | **Yes** |
| A-09 | API parity | **PASS** | E3, E4, E5 | No |
| A-09 | Frontend parity | **BLOCKED** (+ **FAIL** on build) | E8, E9, E10, E11 | **Yes** |
| A-09 | Runtime parity | **PASS** (health-endpoint level) | E1, E2, E22 | No |
| A-09 | Required soak | **FAIL** | E14, E15, E6 | **Yes** |
| OPS01-01 | Offsite backup | **BLOCKED** | E13, E16 | **Yes** |
| OPS01-02 | WAL archive | **BLOCKED** | E13, E17 | **Yes** |
| OPS01-03 | PITR | **BLOCKED** | E18 | **Yes** |
| OPS01-04 | Staging soak | **FAIL** | E14, E15 | **Yes** |
| OPS01-05 | Go-live signatures | **BLOCKED** | E19, E20 | **Yes** |
| OPS01-06 | Neo4j DR | **FAIL** | E12 | **Yes** |
| OPS01-07 | Compose / deployment SoT | **FAIL** | E6, E21 | **Yes** |
| OPS01-08 | RPO / RTO | **FAIL** | E12, E13, E18 | **Yes** |

## Final Decision

# NO-GO

Eleven of thirteen gates are FAIL or BLOCKED, and every one of them is a P0. The two passing gates — API contract parity and health-endpoint runtime — are genuinely clean, and they are the two that measure the least. A GO decision is not available on this evidence, and the gap is not a paperwork gap: production cannot currently build its own frontend, and the graph database has no storage to recover from.

---

## 10. Exact Remaining Actions Required Before Production

**Blocking — must be closed and re-verified**

1. Commit `salesos/frontend/src/lib/company360Signals.ts` (and its test), get a green production Vercel build, and confirm the production alias serves the same commit as the backend. Until then the frontend is unshippable.
2. Add a persistent volume to `neo4j-prod` in production and staging, then implement, execute, and evidence a `neo4j-admin dump` → restore drill with retention. Until a volume exists, OPS01-06 and the graph half of OPS01-08 cannot progress.
3. Separate staging from production deployment. Staging must build from a distinct ref (release branch or tag) and production must be promoted only after staging passes. Same-branch, same-second deploys make every soak requirement unsatisfiable by construction.
4. Reconcile the deployment source of truth: make Railway service settings match `railway.json` (or delete `railway.json` and declare the dashboard authoritative), and record which layer wins.
5. Confirm — with a human, from the Railway console — whether staging and production Postgres share volume `05512e31-396d-447c-b74a-a164792c02b6`. If they do, this is a data-isolation incident that outranks everything else on this list.
6. Run a real ≥48h (prefer 72h) soak against the frozen release commit, in a staging environment that is actually receiving synthetic load, with `soak_complete_claim` flipped only by a human. Idle uptime does not count. Close the M1 RCA for the 2026-08-09 `salesos_app` credential outage first, or it will recur inside the soak.
7. Re-run and capture, dated within the go-live window: (a) an offsite backup + restore-to-disposable drill, (b) `pg_stat_archiver` showing recent archives with `failed_count = 0`, (c) a PITR restore-to-timestamp into an isolated environment. Sign each artifact — `signed_off_by` is empty on all three.
8. Re-ink `SIGN_HERE.md` against a **named commit**, with **two different people** in the CTO and Tech Lead roles, dated **after** items 1–7 produce their evidence. Remove or supersede the contradictory NO-GO/UNSIGNED text in the same file and reconcile `GO-LIVE-SIGNATURE-PACKET.md`.
9. Sign the RPO/RTO acceptance (OPS01-08) only once items 2 and 7 give it something to accept, and state explicitly whether single-region with no DR failover is accepted.

**Non-blocking but do before go-live**

10. Patch `CVE-2026-15741` on Postgres deliberately, in a controlled window, rather than letting the armed auto-update fire unattended against the production database.
11. Re-test production `/login` in a clean Chrome profile with no extensions. If the blank render reproduces, it is a P0 and belongs above this line.
12. Redeploy the staging `celery-worker` to the release commit.
13. Replace the `datetime.now()`-style default on `WorkloadSummary.generated_at` so the OpenAPI document is reproducible.
14. Remove or relocate the quarantined repo-root `docker-compose.yml`.

*Independent verification — read-only. No source, configuration, infrastructure, or data was modified. No secret values are reproduced in this report.*
