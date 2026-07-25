# UX Audit — Legacy FE Baseline

**Scope:** 54 routes (PAGE_MAP). Method: inventory + Wave 13 crawl cross-ref.  
**Label:** light validated — not a full moderated UX study.

## Strengths

- Broad module coverage (CRM, analytics, admin, automation).
- Design-language packages exist (`@salesos/design-language`, `@salesos/ui`).
- Company/Employee 360 pages exist.
- Command palette hook present in shell (`commandOpen`).

## Findings

| ID | Severity | Finding | Recommendation |
|----|----------|---------|----------------|
| UX-01 | High | Flat nav; poor domain grouping | Navigation Principles L1–L5 |
| UX-02 | High | Orphan Knowledge/Marketplace | Promote to Domain nav |
| UX-03 | High | Inconsistent page headers (`no_h1`) | Mandatory PageHeader |
| UX-04 | Med | Duplicate Contacts entry | Deduplicate |
| UX-05 | Med | Landing stub | Redesign auth/marketing separately |
| UX-06 | Med | Dashboards feel static | Dashboard Engine |
| UX-07 | Med | Tables inconsistent | Enterprise Data Grid |
| UX-08 | Med | Soft click timeouts on filters | Motion + robust filter UX |
| UX-09 | Low | Copilot gated but still in IA confusion | AI Experience Preview pattern |
| UX-10 | High | Trust eroded by API errors in crawl | Error/Empty libraries + engines |

## Dead ends

- i18n `nav.nba` → no route.
- Feature drift / RBAC matrix / widget marketplace / signal rule config / path analysis / data quality dashboard — planned-missing.

## Density

Mixed: some workspaces dense, marketing thin, analytics cards uneven. Target: **comfortable density** with Density toggle on grids.
