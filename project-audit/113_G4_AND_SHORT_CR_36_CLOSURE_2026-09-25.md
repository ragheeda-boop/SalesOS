# 113 — G4 (643 accounts) and the 36-account short-CR group reviewed and captured; branch pushed (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026: "يلا ادخل في لوب واغلق G4 (~750 حساباً) مجموعة الـ36 (سجل قصير) Commit / Push"; explicit "نعم" approving the G4 + short-CR methodology and figures presented in chat; explicit "2" choosing to push despite a known pre-existing leaked secret elsewhere in the branch's history (see §4).

**Scope:** `salesos_test` only (capture-only writes to `md_review_queue_state`; no merge, no CR promotion, no classification change). Local git commit + push of code/docs only — the review workbooks themselves are `docs/data/**` and stay git-ignored (real company data), matching every prior session's practice.

## 1. G4 (643 P1 accounts: 234 field-conflict + 112 weak-identity + 297 corroboration-sample)

Individual live web verification for 643 accounts was not attempted (cost/scale). Instead, every row was resolved by one of, in priority order:

1. **Domain-frequency** (the same ≥5-distinct-account "shared/generic domain" rule already established and PO-approved in reports 107/108): resolves cases where exactly one of two conflicting domains is company-specific and the other is shared/generic.
2. **Name-domain text match**: an English company name (from any source) or an Arabic-name Latin-transliteration root textually matching a candidate domain.
3. **Source-reliability tiers already established by this project's own G5 spot checks**: multi-source agreement (0% error, report 111, n=15) and single-source SFDA (1.2% error, report 111, n=81) are treated as confirmed identity absent a conflict.
4. **My own reading** for 32 smaller, non-systematic cases (SINGLE_GENERIC + one-off ambiguous-frequency rows), using real-world business knowledge (e.g., NADEC, Savola/United Sugar Company, Coca-Cola Saudi Arabia, Al-Naghi, Abudawood) alongside name/domain correspondence.
5. **Honest non-verification** for the remainder: no internal signal resolved the row and no live check was performed.

| Decision | Count | Basis |
|---|---:|---|
| CORRECT | 277 | Frequency-clean (20) + alias-same-base (24) + name-token match (39+1) + multi-source (146) + SFDA-single (41) + hand-reviewed (7) |
| MATERIAL_ERROR | 52 | Frequency-flip (2) + name-token mismatch/missing (29+6) + hand-reviewed (15) |
| CANNOT_VERIFY | 314 | No-evidence (55) + hand-reviewed genuinely ambiguous (11) + no internal signal at all (248) |

**Notable MATERIAL_ERROR findings** (all record-only; none applied to `md_global_companies`):
- **MA-0284447** ("Naqel Express"): canonical domain `naqel.com.sa` is the group's shared domain (11 accounts); `naqelexpress.com` is account-specific and name-matching.
- **MA-0278211** ("Fouad Middle East Engineering Consultancy"): canonical domain `alfouadgc.com` is shared (10 accounts); `fg-meeco.com` (Fouad Group Middle East Engineering CO) is the account-specific match.
- **MA-0094662**: `saadeddin.com` belongs to a different, name-matching entity in the same review set (MA-0297286, confirmed by an independent Apollo English name "Saadeddinpastry").
- 13 accounts have **no domain recorded at all** despite strong, well-evidenced candidates (NADEC, Coca-Cola Saudi Arabia, Savola/United Sugar Company, Al-Rashed Foods, Al-Naghi, Al-Muhaid Group, Mayar, and 5 more) — flagged as recommendations only, per the record-only capture contract.
- A likely **duplicate MA record** was flagged (MA-0277764 / MA-0277220, near-identical names, same domain) for a separate dedup review — not merged, per the standing invariant.

**Data-quality artifacts noted, not acted on:** `gmail.com.com`, `outlook.sa`, `5boxes.co` (recurring across ≥2 unrelated accounts), and `sms-fa.com` (recurring across 2 unrelated medical-services accounts) look like generic/placeholder values rather than real company domains — worth a future systematic sweep, out of this review's scope.

Captured via `scripts/phase7a_capture_gate_workbooks.py --apply`: **648/648 recorded** (643 new + the prior 5 G3 short-CR captures re-confirmed idempotently). `md_review_queue_state` (`queue_type='P1_CANDIDATE'`): 277 CONFIRM / 52 ESCALATE / 314 REVIEW — verified directly in the database.

## 2. The 36-account short-CR group — now 36/36 reviewed

31 were pending (5 already captured under the earlier 5-account G3 workbook, report 112, turned out to be members of this same 36-account population). The domains alone gave an unusually clean, self-evident signal:

| Pattern | Count | Decision |
|---|---:|---|
| Government/university domain (`.gov.sa`/`.edu.sa`) | 6 | `NOT_A_CR` — government bodies carry no commercial registration |
| Non-profit/charity domain (`.org`/`.org.sa` + one named "society") | 13 | `NOT_A_CR` — matches the established NCNP short-CR pattern |
| Named religious/charitable foundation CMS subdomain | 1 | `NOT_A_CR` |
| Placeholder/URL-shortener/third-party-service domain (`site.sa`, `org.sa`, `maps.google.com`, `t.co`, `n9.cl`, `2u.pw`) | 6 | `NOT_A_CR` — no evidence of an identifiable commercial entity |
| No domain, or a domain fitting none of the above | 5 | `UNRESOLVED_ESCALATE` — genuinely ambiguous |

No case in this batch was called `CONFIRMED_VALID_SHORT_CR` — the government-ID hard veto (report 91 §4.2) is preserved; nothing was promoted to a valid CR.

Written into `docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv`'s `adjudication`/`reviewer`/`reviewed_at`/`notes` columns, then captured via a small dedicated script (mirrors `phase7a_capture_gate_workbooks.py`'s G3 handling exactly — same `G3_MAP`, same `record_disposition` call — since the existing tool only reads the earlier 5-account workbook). Dry run first (`to_record: 31`, no invalid values), then `--apply` (`recorded: 31`). `md_review_queue_state` (`queue_type='SHORT_CR'`), verified in the database: **29 `CONFIRMED_ARTIFACT` + 7 `UNRESOLVED_ESCALATE` = 36/36, 0 pending.**

## 3. Permission-classifier interactions

Both the G4 workbook write (643 rows) and the 36-account workbook write (31 rows) were initially blocked ("Modify Shared Resources") until the specific content and counts were presented in chat and explicitly approved ("نعم"). Neither was retried through another tool or route while blocked; each proceeded only after a fresh, specific user confirmation matching the blocked action.

## 4. Commit and push

- Commit `afcdbfbd` (7 files: `AGENTS.md`, this report's predecessor `112`, `usability.py` rules I/J, 3 test files, the `/v3/sales-usability` frontend labels) — secret-scanned clean before staging, explicit paths only.
- `git push origin fix/login-and-keys` was initially blocked ("Data Exfiltration") — this branch had never been pushed this session and carries 9 unpushed commits. Flagged to the PO before pushing: this branch's own history (report 100 §3) contains an already-committed, never-pushed HS256 signing token (commit `3de118a5`) that pushing would newly publish to GitHub. PO chose option 2 ("push as-is, address the secret later") with that information disclosed. Push succeeded: `3bfa6adb..afcdbfbd fix/login-and-keys -> fix/login-and-keys`, fast-forward, no force.
- **Outstanding, PO-acknowledged risk:** the HS256 token in `3de118a5` is now live on the public GitHub remote. Rotation and/or history purge remain the PO's decision (report 100 §3), unchanged by this session.

## 5. Status

Gates: G4 and the 36-account short-CR population are **fully captured** (every account has a recorded, evidenced disposition) but **G3 and G4 themselves remain OPEN as gates** — capture is not gate closure (matching the established distinction from report 112 §4): `CANNOT_VERIFY`/`UNRESOLVED_ESCALATE` outcomes are real, honest non-closures, not silent passes. G5(Apollo-only), G2 (2,661 P3 pairs) remain untouched. Production remains **NOT APPROVED**.
