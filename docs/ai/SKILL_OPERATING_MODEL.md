# SKILL OPERATING MODEL — 2026-08-24

**Purpose:** Define required reusable skills, identify gaps, eliminate non-skills.

---

## Active Skills (Repeatable Workflows)

### 1. Repository Audit

| Property | Value |
|----------|-------|
| Purpose | Comprehensive codebase inspection |
| Trigger | Periodic or on-demand |
| Steps | Directory traversal → module inventory → dependency mapping → dead code detection |
| Tools | Glob, Grep, Read, Bash |
| Output | Repository forensics report |
| Status | ACTIVE (demonstrated in Phase 1 reconciliation) |

### 2. Security Re-baseline

| Property | Value |
|----------|-------|
| Purpose | Fresh security assessment |
| Trigger | Post-fix phases, pre-release |
| Steps | Auth → AuthZ → RLS → CSRF → SSRF → PII → Secrets → API security → Gaps |
| Tools | Grep, Read (security-critical files) |
| Output | Security re-baseline report |
| Status | ACTIVE (demonstrated in Phase 2) |

### 3. Test Failure Triage

| Property | Value |
|----------|-------|
| Purpose | Classify test failures by root cause |
| Trigger | After test suite changes |
| Steps | Read triage report → Read conftest → Read failing tests → Classify → Recommend |
| Tools | Read, Grep |
| Output | Test failure register |
| Status | ACTIVE (demonstrated in Phase 2) |

### 4. Migration Validation

| Property | Value |
|----------|-------|
| Purpose | Verify schema migration integrity |
| Trigger | Pre-deploy, CI |
| Steps | List migrations → Verify chain → Check head → Compare with models |
| Tools | Bash (alembic), Read |
| Output | Migration validation report |
| Status | ACTIVE (CI enforced) |

### 5. Documentation Reconciliation

| Property | Value |
|----------|-------|
| Purpose | Identify stale, contradictory, or obsolete documentation |
| Trigger | Periodic or on-demand |
| Steps | Inventory docs → Classify (KEEP/UPDATE/ARCHIVE) → Identify conflicts |
| Tools | Glob, Read, Grep |
| Output | Documentation reconciliation report |
| Status | ACTIVE (demonstrated in Phase 2) |

### 6. Architecture Validation

| Property | Value |
|----------|-------|
| Purpose | Verify code matches documented architecture |
| Trigger | Post-architecture changes |
| Steps | Read ADRs → Read code → Compare → Identify drift |
| Tools | Read, Grep |
| Output | Architecture drift report |
| Status | ACTIVE (demonstrated in Phase 1) |

---

## Gap Skills (Needed But Not Yet Created)

### 7. LLM Provider Qualification

| Property | Value |
|----------|-------|
| Purpose | Evaluate and qualify LLM providers for production |
| Trigger | Before AI GA |
| Steps | Provider setup → SLA testing → Cost measurement → Security review → Qualify/reject |
| Tools | API calls, monitoring |
| Output | Provider qualification report |
| Status | **NEEDED** — AI Horde is DEV-ONLY, no commercial provider qualified |

### 8. Load/Stress Testing

| Property | Value |
|----------|-------|
| Purpose | Validate SLO targets under load |
| Trigger | Pre-production |
| Steps | Load test design → Execution → Analysis → SLO validation |
| Tools | k6, locust, or similar |
| Output | Load test report |
| Status | **NEEDED** — SLO targets proposed but never measured |

### 9. External Pentest Preparation

| Property | Value |
|----------|-------|
| Purpose | Prepare for external penetration testing |
| Trigger | Before pentest engagement |
| Steps | Scope definition → Target inventory → Test environment setup → Findings remediation |
| Tools | Manual |
| Output | Pentest preparation package |
| Status | **NEEDED** — No external pentest started |

### 10. Release Readiness Check

| Property | Value |
|----------|-------|
| Purpose | Pre-release gate validation |
| Trigger | Before any release |
| Steps | Security check → Test check → Migration check → Config check → Documentation check |
| Tools | All |
| Output | Release readiness report |
| Status | **NEEDED** — No automated release readiness skill |

---

## Non-Skills (Eliminated)

| Concept | Why Not a Skill |
|---------|----------------|
| "Code review" | Not a repeatable automated workflow; human judgment required |
| "Documentation sync" | Part of documentation reconciliation skill |
| "Deployment" | Infrastructure-specific, not a general skill |
| "Monitoring setup" | Infrastructure-specific |

---

## Skill Priority

| Priority | Skill | Status |
|----------|-------|--------|
| P0 | Repository Audit | ACTIVE |
| P0 | Security Re-baseline | ACTIVE |
| P0 | Test Failure Triage | ACTIVE |
| P1 | Migration Validation | ACTIVE |
| P1 | Documentation Reconciliation | ACTIVE |
| P1 | Architecture Validation | ACTIVE |
| P1 | LLM Provider Qualification | **NEEDED** |
| P2 | Load/Stress Testing | **NEEDED** |
| P2 | External Pentest Preparation | **NEEDED** |
| P2 | Release Readiness Check | **NEEDED** |
