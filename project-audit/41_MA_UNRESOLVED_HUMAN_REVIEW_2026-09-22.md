# MA Unresolved Human Review — 2026-09-22

## Decision

The 1,114 unresolved v0.7 contact links were checked against the official
Master Accounts snapshot (296,746 companies). This is a deterministic review
manifest only. No `Global_Company_ID` was written to v0.7, no source row was
changed, and no production database was touched.

| Result | Rows |
|---|---:|
| `DETERMINISTIC_EXACT_NAME_DOMAIN` — exact normalized organization name + exact email domain, with no MA-level conflict | 412 |
| `REVIEW_UNIQUE_DOMAIN` — domain is unique but name does not corroborate | 242 |
| `REVIEW_UNIQUE_NAME` — name is unique without exact domain corroboration | 114 |
| `ESCALATE_DOMAIN_AMBIGUOUS` | 133 |
| `ESCALATE_NAME_AMBIGUOUS` | 4 |
| `ESCALATE_NO_DETERMINISTIC_CANDIDATE` | 76 |
| `ESCALATE_MA_MULTI_CANDIDATE` — one legacy MA key maps to multiple current Global IDs | 133 |
| **Total** | **1114** |

The **412 exact name+domain rows** are the only rows with a deterministic
candidate and no MA-level conflict in this pass. A further **133 rows across
7 legacy MA keys** were deliberately escalated because the same stale MA key
points to multiple current Global IDs. They must be split before any mapping
is applied. All candidates remain proposals until a data-owner disposition is
recorded; the manifest does not apply them. Domain-only and name-only matches
remain review items because group domains and repeated names can identify
different legal entities.

## Evidence

- v0.7 input: `C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.7.csv`
- v0.7 SHA-256: `9772be62111ff40d664678de497449d7134e4def7e01057494bcddae88b5c9ec`
- Master snapshot: `salesos_test.md_global_companies` from `01_Master_Accounts.csv`
- Master population checked: 296,746
- Output SHA-256: `139122198e5e6815ef75e774840b8e1cfcaed943916a09592a640fa007cade15`
- Output: `D:\AISalesOS\project-audit\41_MA_UNRESOLVED_HUMAN_REVIEW_2026-09-22.csv`

**Safety:** no database writes; no external calls; no guessed mappings; no
Global ID stability risk. Roadmap: **75% (85/113)**.
