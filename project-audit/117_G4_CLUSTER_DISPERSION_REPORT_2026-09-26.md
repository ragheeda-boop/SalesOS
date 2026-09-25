# 117 — G4 corroboration cluster / verdict dispersion (report 116 W7b)

**Read-only.** Reproduces report 116 SS6.2's cluster-and-certify falsification against the live `salesos_test` database and persists it (it previously existed only as console output). No write, no merge, no classification change.

Population: **5,903** P1 `CORROBORATION_REVIEW` candidates (active, non-superseded). Clustered by evidence signature `('best_match_confidence', 'cr_class', 'field_conflict', 'real_domain_present', 'apollo_account_present')`.

Distinct evidence signatures: **14**.

Rows with a captured disposition: **297** of 5,903.


## Cumulative coverage of the largest clusters

| Rank | Cluster size | Cumulative | % of population |
|---:|---:|---:|---:|
| 1 | 1,697 | 1,697 | 28.7% |
| 2 | 1,480 | 3,177 | 53.8% |
| 3 | 1,154 | 4,331 | 73.4% |
| 4 | 660 | 4,991 | 84.6% |
| 5 | 441 | 5,432 | 92.0% |
| 6 | 405 | 5,837 | 98.9% |
| 7 | 30 | 5,867 | 99.4% |
| 8 | 15 | 5,882 | 99.6% |
| 9 | 7 | 5,889 | 99.8% |
| 10 | 6 | 5,895 | 99.9% |

## Every cluster with more than one reviewed verdict (mixed = not certifiable)

**4** of 14 clusters have MIXED verdicts among their reviewed members — the same evidence signature produced different human/agent judgments, so no deterministic rule keyed on this signature alone can replace individual review for these clusters.

| Signature (confidence, cr_class, field_conflict, real_domain, apollo) | size | CORRECT | MATERIAL_ERROR | CANNOT_VERIFY | not reviewed |
|---|---:|---:|---:|---:|---:|
| `('MATCHED', 'SAFE', False, True, False)` | 1,697 | 48 | 11 | 28 | 1,610 |
| `('LIKELY MATCH', 'AMBIGUOUS', False, True, True)` | 1,480 | 70 | 0 | 1 | 1,409 |
| `('MATCHED', 'SAFE', False, False, False)` | 1,154 | 2 | 1 | 53 | 1,098 |
| `('MATCHED', 'SAFE', False, True, True)` | 405 | 24 | 1 | 2 | 378 |

## error_type completeness among reviewed rows

Of 297 rows with a captured disposition, **284** carry no `error_type` at all in their evidence_ref — the reasoning behind the verdict was never captured, which is exactly why no deterministic rule can be reverse-engineered from the reviewed sample: the missing ingredient is not a smarter clustering key, it is the reason itself. Report 116 W1 makes `reason` mandatory going forward; this does not retroactively fill in these rows.


## Conclusion

Cluster-and-certify (bulk-applying one verdict per evidence-signature cluster) is **not viable** for the G4 P1 corroboration backlog: the largest clusters are exactly the ones with mixed verdicts, so certifying by signature would apply the wrong verdict to a material fraction of any large cluster. The remaining backlog needs individual review, or new evidence (e.g. a live source check) that the current signature does not capture — not a shortcut around the review itself. This reproduces and persists report 116 SS6.2's finding; no gate is closed by this report.

