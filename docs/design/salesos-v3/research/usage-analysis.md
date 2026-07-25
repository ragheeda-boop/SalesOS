# Feature Usage Analysis

> **Honest gap:** No product analytics warehouse for clickstreams. Analysis is **route inventory + crawl**, not measured adoption.

## Inventory snapshot (legacy FE)

| Class | Count | Notes |
|-------|------:|-------|
| App Router pages | 54 | PAGE_MAP |
| Primary nav destinations | ~25 unique | duplicate Contacts |
| Wave 13 crawl shells | 49/49 PASS | entity `[id]` skipped |
| planned-missing | 7 | NBA, path analysis, feature drift, data quality, widget marketplace, signal rules, RBAC matrix |
| orphaned-code | 4 | `/knowledge*`, `/marketplace*` |
| implemented-stub | 4 | `/`, gated copilot, demo honesty notes |

## Likely high-traffic (hypothesis)

`/dashboard`, `/companies`, `/opportunities`, `/pipeline`, `/employees`, `/search`, `/settings`, `/admin`.

## Likely low-discoverability

`/knowledge`, `/knowledge/connectors`, `/marketplace`, deep `/admin/*`, `/copilot/telemetry`.

## Telemetry requirements (Phase 8+)

- Page views, CmdK invocations, search success, widget render, task completion.
- Until then: mark adoption metrics **UNKNOWN**.
