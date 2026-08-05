# 06 — Findings Schema | مخطط النتائج

**Pack:** Enterprise Audit Board v2.1  
**Role:** Normalized finding records for every run  
**Status:** Binding schema — instances empty until a run

---

## 1. Finding ID format

```text
{AXIS_PREFIX}-{SEQ}
```

- `AXIS_PREFIX` — from [02-METHODOLOGY.md](./02-METHODOLOGY.md) (e.g. `SEC`, `DTM`, `DRIFT`, `ECON`, `AIGOV`)  
- `SEQ` — zero-padded integer within the run (`001`, `002`, …)  
- Optional run tag: `EAB-2026-MM-DD/SEC-001` when citing across documents  

Examples: `AG-001`, `DTM-003`, `AIGOV-012`, `GO-001`

---

## 2. Severity

| Severity | Meaning | Typical action |
|----------|---------|----------------|
| **P0** | Blocks Production GA / pilot; security or honesty breach | Must close before any GO / pilot claim |
| **P1** | High risk or major governance gap | 30-day recovery priority |
| **P2** | Material debt / drift / economics Extreme hotspot | 60-day structural |
| **P3** | Moderate; tracked | 90-day / roadmap |
| **P4** | Low / hygiene | Backlog |

Do not inflate severity to force GO narratives. Do not bury P0 under “tech debt.”

---

## 3. Root cause vs symptom

Every finding **must** separate:

| Field | Rule |
|-------|------|
| **Symptom** | Observable failure (e.g. “middleware no-ops when factory unset”) |
| **Root cause** | Structural reason (e.g. “fail-open design; no closed default”) |
| **If unknown** | Set `root_cause: unknown — needs investigation` — do not invent |

Symptoms alone are insufficient for Axes 40–42 (traceability, drift, economics).

---

## 4. Required fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Per §1 |
| `title` | string | One line |
| `axis` | int[] | Axis numbers (e.g. `[30]`, `[40,41]`) |
| `axis_tags` | string[] | Prefixes (`SEC`, `DTM`) |
| `severity` | P0–P4 | |
| `symptom` | string | |
| `root_cause` | string | Or unknown |
| `evidence` | string[] | Paths, commands, agent IDs |
| `validation_label` | enum | From [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md) |
| `recommendation` | string | Actionable |
| `owner` | string | Role or team; `unassigned` ok |
| `status` | open / waived / closed | Waivers need ticket + expiry |
| `related_ids` | string[] | Optional links |
| `economics_band` | Low/Med/High/Extreme / n/a | Required when axis includes 42 |
| `drift_metric_ids` | string[] | Optional DM-* from fitness catalog |

---

## 5. Axis tags (v2.1)

Tag findings with **all** applicable axes. Cross-cutting examples:

| Pattern | Tags |
|---------|------|
| Stub marketed as live AI | `AIA`, `AIGOV`, `FE`, maybe `CEO` |
| Accepted ADR not in code | `ADR`, `DRIFT`, `DTM` |
| Dual decision engines | `DUP`, `DRIFT`, `ECON`, `BR` |
| Missing DTM hop | `DTM`, maybe `CAP` / `TST` / `OPS` |

---

## 6. Record template (copy per finding)

```yaml
id: PREFIX-001
title: ""
axis: []
axis_tags: []
severity: P2
symptom: ""
root_cause: ""
evidence: []
validation_label: not validated
recommendation: ""
owner: unassigned
status: open
related_ids: []
economics_band: n/a
drift_metric_ids: []
```

---

*Findings Schema — Enterprise Audit Board v2.1*
