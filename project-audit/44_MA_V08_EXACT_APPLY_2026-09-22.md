# MA v0.8 Exact Apply — 2026-09-22

## Result

Created the derived final file:

`C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.8.csv`

Applied **412** exact name+domain proposals from the reviewed v0.8 proposal
file. The official v0.7 file was not overwritten and its SHA-256 remained
`9772be62111ff40d664678de497449d7134e4def7e01057494bcddae88b5c9ec`.

| Check | Result |
|---|---:|
| Rows preserved | 47,192 / 47,192 |
| Exact proposals applied | 412 |
| Remaining unresolved/review rows | 702 |
| Official v0.7 modified | No |
| Database writes | 0 |
| Production writes | 0 |
| External calls | 0 |

Applied rows use `Linkage_Status=RESOLVED_VIA_EXACT_NAME_DOMAIN_MASTER_V10`. All other unresolved rows
retain blank `Global_Company_ID` and their explicit non-applied status.

- Proposal input SHA-256: `330fc5c429aa4c85b9b60bd44a13dce8932759247bbee27de5a7e9237ce680c9`
- Derived v0.8 SHA-256: `a64f669f45b5e816241ac15b1e5ed210a2c4d0bd94e383e42d1f0436f1c9d372`
- Machine-readable evidence: `44_MA_V08_EXACT_APPLY_2026-09-22.json`

This derived file is ready for a separate data-quality check; it is not a
production ingestion or database migration.

**Roadmap: 75% (85/113).**
