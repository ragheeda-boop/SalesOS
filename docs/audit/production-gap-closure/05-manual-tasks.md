# Manual Tasks — Require Human or External Action

**These tasks CANNOT be executed by OpenCode.** They require human decisions, external systems, credentials, or physical access.

---

## M1: Cloud Staging Unblock

**Blocker:** B2  
**Category:** External Dependency / Infrastructure  

**Current state:**  
- `deploy-staging.yml` workflow EXISTS (352 lines, complete)  
- `runbooks/staging-fill-in.md` runbook EXISTS  
- `docker-compose.staging.yml` (445 lines) EXISTS  
- `probe-2026-07-22T163200Z.json` proves: 0 GitHub Environments, 0 secrets, workflow 404 on master, develop branch absent  

**What must happen:**

1. **Create `develop` branch** in GitHub (if not exists).
2. **Create GitHub Environment** named `staging` with the following secrets:
   - `STAGING_HOST` — VPS IP or hostname
   - `STAGING_USER` — SSH user (e.g., `deploy`)
   - `STAGING_SSH_KEY` — Private SSH key with access to VPS
3. **Provision VPS** (or prepare existing) with:
   - Docker + Docker Compose
   - SSH access configured
   - Open ports: 22 (SSH), 80, 443 (or alternate)
   - Sufficient disk for images + DB (~50 GB safe)
4. **Push `deploy-staging.yml`** to the `develop` branch (or reconfigure trigger).
5. **Trigger deploy** manually or via push to `develop`.
6. **Verify:**
   - Backend health: `curl https://staging.$DOMAIN/health` → `{"status":"ok"}`
   - Pre-deploy gates PASS (`pre-deploy-gates.ps1` on staging)
   - Frontend loads at `https://staging.$DOMAIN`
   - Smoke auth 13/13 PASS
7. **Execute deploy → rollback tabletop:**
   - Deploy new image → verify health → smoke → rollback to previous image → verify health
   - Capture evidence JSON

**Owner:** DevOps / Infrastructure Engineer  
**Estimated effort:** 4-8 hours (provisioning + configuration + testing)  
**Dependencies:** VPS access, GitHub admin access, domain DNS configuration  

---

## M2: CTO + Tech Lead Signatures

**Blocker:** B4  
**Category:** Governance  

**Current state:**  
- `SIGN_HERE.md` prepared with full blocker list and evidence links  
- CTO block has `Status: SIGNED` (contradictory with blank Date/Signature)  
- Tech Lead block has `Status: SIGNED` (same contradiction)  
- Both Decision fields blank  
- Evidence-reviewed box unchecked  

**What must happen:**

1. **CTO reviews** the complete evidence package (or delegates review).
2. **Tech Lead reviews** the complete evidence package.
3. Both complete `SIGN_HERE.md`:
   - Set `Decision:` to `GO`, `NO-GO`, or `CONDITIONAL` (not `[ ok] GO` placeholder)
   - Fill `Date:` with actual date
   - Check `[x] Yes` for evidence reviewed (or `[ ] No`)
   - Write conditions if CONDITIONAL
   - Provide actual signature or acknowledgment
4. If NO-GO: document which conditions must change
5. If CONDITIONAL: list exact conditions that must be met before GO

**Owner:** CTO (ragheed) and Tech Lead (ragheed)  
**Estimated effort:** 1-2 hours review + signature  
**Dependencies:** Phase 1 + Phase 2 evidence package must be ready for review  

**IMPORTANT:** The current `Status: SIGNED` with blank fields is contradictory. The signers must either:
- Fill all fields and genuinely sign, OR
- Clear the `SIGNED` status if not yet ready to sign

---

## M3: RPO Acceptance

**Blocker:** B11  
**Category:** Governance  

**Current state:**  
- RPO target UNSIGNED  
- Two options documented:
  - **Option A:** 24h RPO (daily backup) — simpler but up to 24h data loss
  - **Option B:** WAL-based (~0 data loss) — requires `archive_mode=on` on primary + PITR restore capability  

**What must happen:**

1. CTO selects RPO target.
2. If Option A: sign acceptance of 24h max data loss window.
3. If Option B: approve infrastructure changes:
   - Enable `archive_mode=on` on production Postgres
   - Implement WAL archiving to offsite storage (S3/MinIO)
   - Verify PITR restore capability monthly
4. Document accepted RPO in `PROGRESS-WAVE10-DR-GAPS.md` or standalone RPO acceptance document.
5. Sign or acknowledge in writing.

**Owner:** CTO  
**Estimated effort:** 30 minutes decision + documentation  
**Dependencies:** Technical recommendation from DBA/DevOps on WAL feasibility  

---

## M4: AI Honesty PRC Sign-off

**Blocker:** B12  
**Category:** Governance  

**Current state:**  
- Code/docs gate DONE:
  - `feature_ai_copilot` default `False` (config.py:76)
  - Copilot API returns 403 when flag False
  - FE Decision Engine is STUB (throws)
  - Nav/panel hidden when flag off
  - Preview badges added
- Human PRC (Production Readiness Committee) review still **OPEN**

**What must happen:**

1. CTO + Product lead review `AI_HONESTY.md`.
2. Confirm launch messaging does NOT describe AI features as production-capable.
3. Confirm `feature_ai_copilot=False` is the default in production.
4. Approve or reject AI-related launch notes.
5. Document sign-off in `AI_HONESTY.md` or via email/acknowledgment.

**Owner:** CTO + Product  
**Estimated effort:** 30 minutes review  
**Dependencies:** Launch notes draft  

---

## M5: Staging Pentest

**Blocker:** B5  
**Category:** External Security Validation  

**Current state:**  
- P0 security fixes code-complete:
  - IDOR (Decision Center tenant-scoped)  
  - SSRF (HTTPS + private block + pin-on-connect)  
  - KG SQL fallback tenant filters  
  - Forecast demo gate  
- Security score: **48/100** (baseline audit)
- Deployed to local; cloud staging BLOCKED (M1)
- SSRF residuals documented (DNS TOCTOU, first-IP only, httpx pool coupling)
- `production_secure_claim: false`

**What must happen:**

1. **Unblock cloud staging** (M1 must complete first).
2. Engage security team or external pentest provider.
3. Scope: Production-representative staging environment.
4. Test:
   - SSRF (full matrix, DNS rebinding, IPv6, redirect chains)
   - Tenant isolation (header injection, IDOR, cross-tenant API access)
   - Authentication (JWT manipulation, refresh token, CSRF, rate limiting)
   - RBAC (role escalation, permission bypass)
   - GraphQL injection
   - API gateway / CORS / CSP headers
   - Observability data exposure
5. Remediate critical/high findings.
6. Produce pentest report with findings and remediation evidence.
7. Sign residual acceptance for any accepted risks.

**For expedited pilot (alternative to full pentest):**
- Accept current P0 code fixes as sufficient for pilot scope
- Document accepted residual risks explicitly
- CTO and Security sign residual acceptance
- Plan full pentest before production GA

**Owner:** Security team or external provider  
**Estimated effort:** 2-4 weeks for full pentest; 1-2 days for pilot residual acceptance  
**Dependencies:** M1 (cloud staging must be accessible)  

---

## M6: Launch Hygiene Preparation

**Blocker:** B13  
**Category:** Governance / Operations  

**Current state:**  
- `runbooks/go-live-checklist.md` EXISTS with T-7/T-3/T-1/T-0/T+1 schedule
- `runbooks/hypercare-14d.md` EXISTS with staffing and checklist
- BUT none of the T-7/T-1 items are checked off

**What must happen:**

### T-7 (7 days before GO):
1. **Feature freeze**: No new features merged to `develop` without exception approval.
2. **On-call roster**: Publish 14-day on-call schedule with escalation path.
3. **Production backup**: Schedule daily 03:00 backup cronjob (K8s `backup-cronjob.yaml` or compose equivalent).
4. **Staging RC digests**: Confirm image digests for staging release candidate.
5. **SSL certificates**: Verify production SSL certs provisioned (via Caddy or manual).

### T-3 (3 days before GO):
1. **Soak acceptance**: 48h soak results reviewed and accepted by Tech Lead.
2. **Staging smoke**: Full staging smoke test results reviewed.
3. **Rollback validated**: Staging rollback tabletop completed successfully.

### T-1 (1 day before GO):
1. **Final pre-deploy gates PASS** on staging.
2. **Backup verified**: Most recent backup restored to disposable DB, verified.
3. **Communication**: Stakeholders notified of maintenance window.
4. **Go/No-Go call**: Final meeting with CTO/TL/Security.

### T-0 (GO day):
1. **Production backup** taken immediately before migrate.
2. **Alembic upgrade head** executed on production.
3. **Smoke tests** executed on production.
4. **Monitoring verified** on production.
5. **On-call handoff** confirmed.

### T+1 (day after GO):
1. **24h health check**: No critical incidents.
2. **SLA review**: Error rates, latency within bounds.
3. **User feedback**: Collect early user reports.

**Owner:** Tech Lead + Operations  
**Estimated effort:** 1-2 hours to set up, then ongoing through launch cycle  
**Dependencies:** All other blockers closed before T-7 starts  

---

## Manual task summary

| Task | Blocker | Who | Effort | When |
|------|---------|-----|--------|------|
| M1: Cloud staging unblock | B2 | DevOps | 4-8h | ASAP |
| M2: Signatures | B4 | CTO + TL | 1-2h | After Phase 1+2 |
| M3: RPO acceptance | B11 | CTO | 30min | Anytime |
| M4: AI PRC sign-off | B12 | CTO + Product | 30min | Anytime |
| M5: Pentest | B5 | Security | 2-4 weeks | After M1 |
| M6: Launch hygiene | B13 | TL + Ops | Ongoing | T-7 through T+1 |
