# MA v0.8 Proposal Build — 2026-09-22

## Delivered artifact

Created a derived proposal file:

`C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_PROPOSED_v0.8.csv`

The official `03_Master_Contacts_FINAL_v0.7.csv` was read-only and remains
unchanged. The proposal contains the original 47,192 rows plus four explicit
proposal columns:

- `Proposed_Global_Company_ID`
- `Proposed_Linkage_Status`
- `Proposed_Linkage_Reason`
- `Proposal_Manifest_SHA256`

## Proposal policy

Only the **412** rows with exact normalized organization name + exact email
domain and no MA-level conflict receive a proposed Global Company ID. They
represent 82 consistent legacy MA groups. No proposed ID is applied to the
official file or database.

| Proposal status | Rows |
|---|---:|
| `PROPOSED_EXACT_NAME_DOMAIN_NO_MA_CONFLICT` | 412 |
| `NOT_APPLIED_REVIEW_UNIQUE_DOMAIN` | 242 |
| `NOT_APPLIED_REVIEW_UNIQUE_NAME` | 114 |
| `NOT_APPLIED_ESCALATE_DOMAIN_AMBIGUOUS` | 133 |
| `NOT_APPLIED_ESCALATE_MA_MULTI_CANDIDATE` | 133 |
| `NOT_APPLIED_ESCALATE_NAME_AMBIGUOUS` | 4 |
| `NOT_APPLIED_ESCALATE_NO_DETERMINISTIC_CANDIDATE` | 76 |
| `UNCHANGED_EXISTING_LINK` | 44,974 |
| `NOT_APPLICABLE_NO_ACCOUNT_LINK` | 1,104 |

## Integrity

- Input v0.7 SHA-256: `9772be62111ff40d664678de497449d7134e4def7e01057494bcddae88b5c9ec`
- Output SHA-256: `330fc5c429aa4c85b9b60bd44a13dce8932759247bbee27de5a7e9237ce680c9`
- Rows preserved: 47,192 → 47,192
- Database writes: 0
- Production writes: 0
- External calls: 0

The companion machine-readable manifest is
`project-audit/43_MA_V08_PROPOSAL_BUILD_2026-09-22.json`.

This v0.8 file is a review/proposal artifact, not an approved production
dataset. Applying the 412 proposals is the next controlled operation after
formal data-owner disposition. A capture-only `MA_UNRESOLVED` queue now holds
all 1,114 decisions in `salesos_test`: 412 `CONFIRM_EXACT`, 356 `REVIEW`, and
346 `ESCALATE`. The queue does not apply any mapping.

Phase 7 focused regression after the new queue: **29/29 passed**.

**Roadmap: 75% (85/113).**
