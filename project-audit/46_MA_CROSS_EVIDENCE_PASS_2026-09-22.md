# MA Cross-Evidence Pass — 2026-09-22

The 355 rows remaining after exact name/domain and Apollo passes were checked
using two independent local signals: an exact Apollo Account ID candidate and
an exact normalized organization name plus email domain candidate.

| Result | Rows |
|---|---:|
| `APOLLO_AND_EXACT_NAME_DOMAIN_CORROBORATED` applied to v1.0 | 33 |
| `REVIEW_CROSS_EVIDENCE_CONFLICT` | 0 |
| `ESCALATE_CROSS_EVIDENCE_UNRESOLVED` | 322 |
| **Total** | **355** |

Derived v1.0 contains the previous 759 resolutions plus the newly applied
cross-evidence rows. No database, official v0.7, production, or external
provider write occurred.

The `MA_UNRESOLVED` review queue was refreshed in `salesos_test` from this
manifest: 33 rows are recorded as `CONFIRM_EXACT` and 322 as `ESCALATE`.
The write is capture-only and leaves the Phase 6 Master Data tables unchanged
(296,746 companies, 1,124 people, 909,967 source rows, 54,185 review
candidates).

- v0.9 SHA-256: `d33826aeec402810e71654e8ceda46c9038f5a393bc890a13b04427d50624a9b`
- v1.0 SHA-256: `57ac4987dea2af7aa14f2db19aef6b0c15b827cf532d244bdb06072cb0fa9782`
- Manifest SHA-256: `d5ddd214655ee548713b7343a34a096b4f78e6d7fcb7a431e21c6f129d9ce518`

**Roadmap: 75% (85/113).**
