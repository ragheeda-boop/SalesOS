# Evidence — STORY-14-04 (penetration test)

> **Honesty:** In-repo pack evidence only. Not Production GO. Not zero-criticals.  
> Firm report artifacts (when received) land here **redacted** or as pointers — never commit raw secrets.

## Index

| Artifact | Path / URL | Label |
|----------|------------|-------|
| Pack README | `salesos/docs/pentest/README.md` | light (docs) |
| Brief v1.1 | `salesos/docs/pentest/PENTEST_BRIEF.md` | light (docs) |
| Threat model | `salesos/docs/pentest/THREAT_MODEL.md` | light (docs) |
| Internal test plan | `salesos/docs/pentest/INTERNAL_TEST_PLAN.md` | light (docs) |
| Findings tracker | `salesos/docs/pentest/FINDINGS_TRACKER.md` | FE-SEC-02/03/04 Open residual; FE-SEC-01 Fixed @ `34f4a81` — AC **not validated** |
| FE CSRF support crumb | `docs/program/PHASE1_FE_S14_04_05_CSRF_AUTH_SURFACE_CRUMB.md` | tip `34f4a81` — ≠ story close |
| Vendor handoff | `salesos/docs/pentest/VENDOR_HANDOFF_CHECKLIST.md` | light (docs) |
| Results template | `salesos/docs/pentest/PENTEST_RESULTS_TEMPLATE.md` | template |
| Pack integrity harness | `salesos/scripts/story_14_04_inrepo_pentest_pack.py` | light when exit 0 |
| DevOps CI/Deploy pack | `docs/program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md` | build validated (CI URLs @ `4754b8b`) |
| BE support | `docs/program/PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md` | docs tip `d0070fa` |
| Staging SSRF runbook | `docs/audit/ga-engineering-audit/runbooks/staging-ssrf-pentest.md` | residual-external |
| Wave2 SSRF evidence (legacy path) | `docs/audit/ga-engineering-audit/evidence/wave2-pentest/` | use when staging run executes |

## Tip-line security gate pointers (from DevOps pack @ `4754b8b`)

| Workflow | Conclusion | URL |
|----------|------------|-----|
| Security Scan | SUCCESS | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835461517 |
| CI Stages 1–5 | SUCCESS | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457682 |
| Deploy + Health Gate | SUCCESS | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457753 |
| Stage 6 GHCR | SKIPPED (DEC-150) | same CI run |

## Firm report drop zone

Place redacted summaries as:

- `FIRM_REPORT_SUMMARY.md` (no secrets, no full exploit PoCs against prod)
- `RETEST_NOTES.md`

Raw scanner projects: store offline / encrypted — do not commit `.burp` / credentialed ZAP DBs.

## Validation snapshot

| Claim | Label |
|-------|-------|
| In-repo pack landed | **CLOSED (in-repo) / IN_REPO_READY** |
| External firm pentest | **residual-external** |
| Zero unresolved criticals | **not validated** |
| Production GO | **not claimed** |
