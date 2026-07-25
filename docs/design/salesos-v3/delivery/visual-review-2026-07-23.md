# Visual review — SalesOS shell layout (2026-07-23)

**Scope:** Primary FE `:3000` (`salesos-frontend-1`). Layout / shell sanity only.  
**Verdict:** **PASS** (layout checks). Not Production GO.  
**Validation:** light validated (Playwright headless screenshots + DOM geometry; browser MCP unavailable).  
**Auth:** demo `admin@salesos.io` via `POST /api/v1/identity/login` (password from seed env / default; not recorded here).  
**FE rebuild:** not required (no FAIL).

## Checks

| # | Check | Result | Evidence |
|---|--------|--------|----------|
| 1 | `/companies` — sidebar edge-docked (LTR start = left), content fills rest, no empty column, sidebar not mid-viewport | **PASS** | `screenshots-2026-07-23/companies.png` — aside `left=0`, `w=256`; main `left=256`, `w=1184`; gap=0 |
| 1b | `/companies` RTL (`salesos-locale=ar`) — sidebar on start (right), content fills rest | **PASS** | `screenshots-2026-07-23/companies-rtl.png` — aside `right=1440`, `left=1184`; main `w=1184`; gap=0 |
| 2 | `/v3` shell — same sanity; Ask AI is button/popup not page rail | **PASS** | `screenshots-2026-07-23/v3.png`, `v3-ask-ai-open.png` — one nav aside; Ask AI opens `[role=dialog]` overlay |
| 2b | `/v3` RTL | **PASS** | `screenshots-2026-07-23/v3-rtl.png` — aside docked at right edge; gap=0 |
| 3 | `/v3/companies` — same shell; Ask AI popup | **PASS** | `screenshots-2026-07-23/v3-companies.png`, `v3-companies-ask-ai-open.png` |

## Geometry summary (1440×900)

- LTR `/companies`: aside 0–256, main 256–1440  
- RTL `/companies`: aside 1184–1440, main 0–1184  
- LTR `/v3*`: aside 0–224, main 224–1440  
- Ask AI: topbar button → modal dialog; no second permanent aside/rail

## Notes / limitations

- Browser MCP could not open a tab; used Playwright against `http://127.0.0.1:3000` (host `localhost` IPv6 flaky).  
- Login form UI path was rate-limited (429) after probes; review used API token seed into `localStorage` (same pattern as FE e2e).  
- Company table/data still loading in some frames — out of scope for shell layout.  
- **Not claimed:** browser pass beyond these routes, Production GO, or full test suite.

## Artifact paths

All under `docs/design/salesos-v3/delivery/screenshots-2026-07-23/`:

- `companies.png`, `companies-rtl.png`
- `v3.png`, `v3-rtl.png`, `v3-ask-ai-open.png`
- `v3-companies.png`, `v3-companies-ask-ai-open.png`
- `report.json`, `rtl-report.json`
