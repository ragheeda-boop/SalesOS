# Design Ops

Figma-ready handoff for **SalesOS DS v3** (no Figma API). Artifacts below are importable / checklist-driven for designers.

## Do this today

Cannot drive Figma Desktop from engineering — designers complete this in one sitting:

1. Open [`FIGMA_BUILD_CHECKLIST.md`](./FIGMA_BUILD_CHECKLIST.md) and work top-to-bottom.
2. Create file **SalesOS DS v3** (pages: Foundations · Components · Patterns · Dashboards · Templates).
3. Import Variables from [`tokens.figma.json`](./tokens.figma.json) (collections: Color/Light · Color/Dark · Space · Radius · Typography).
4. Build core components from [`figma-component-inventory.md`](./figma-component-inventory.md) (atoms → Dialog/`AskAIPopup` → DataGrid → Shell helpers).
5. Draft the **8 priority frames** in order:  
   Login → Shell → Sales Home → Company List → Company 360 → Deal 360 → Data Grid → **Ask AI popup**.  
   Specs: [`figma-frames-priority.md`](./figma-frames-priority.md).
6. Remember: **Ask AI is modal only** — overlay with scrim; never a docked rail or layout region ([`../ai/ai-experience.md`](../ai/ai-experience.md)).
7. Stop at Design Review gate before publishing the library ([`review-release.md`](./review-release.md)).

Brand anchors: orange `#F57C1E` (CTA) · muted `#8C8374` (contrast-safe light text).  
Ask AI size tokens: `space/ai-popup` = 512 · `space/ai-popup-max-h` = 640.

## Artifacts (this folder)

| Path | Purpose |
|------|---------|
| [`FIGMA_BUILD_CHECKLIST.md`](./FIGMA_BUILD_CHECKLIST.md) | **Start here** — create file → import variables → components → priority frames |
| [`tokens.figma.json`](./tokens.figma.json) | Figma Variables collections: Color/Light, Color/Dark, Space, Radius, Typography |
| [`figma-component-inventory.md`](./figma-component-inventory.md) | Every DS component → Figma names, variants, states checklist |
| [`figma-frames-priority.md`](./figma-frames-priority.md) | Frames to build first + layout notes (incl. Ask AI popup) |
| [`figma-library.md`](./figma-library.md) | Library structure + **exact Variables → publish** steps |
| [`token-code-sync.md`](./token-code-sync.md) | Token ↔ code pipeline |
| [`review-release.md`](./review-release.md) | Design Review → DS Approval → FE → Design QA |

## Quick start — Variables → publish library

1. Create Figma file **SalesOS DS v3** with pages Foundations · Components · Patterns · Dashboards · Templates.  
2. Import or manually recreate Variables from [`tokens.figma.json`](./tokens.figma.json) (collections named exactly as in the file).  
3. Build components per [`figma-component-inventory.md`](./figma-component-inventory.md).  
4. Build priority frames per [`figma-frames-priority.md`](./figma-frames-priority.md) (Ask AI = modal overlay).  
5. Design Review → **Publish library** from approved `main` (full steps: [`figma-library.md`](./figma-library.md)).  
6. Enable the library in product files; keep Figma ↔ code in sync via [`token-code-sync.md`](./token-code-sync.md).

## Figma Library
Foundations, components, patterns, dashboard widgets. Branching: `main` / `feat/*`.

## Variables
Mirror DS tokens (color, space, type, radius) — see `tokens.figma.json`.

## Code Sync
Tokens → CSS variables / Tailwind theme via pipeline; breaking changes semver.

## Review Workflow
Design Review → DS Approval → FE implement → Design QA.

## Release Workflow
Changelog · version bump · deprecation notices · PROGRAM link.

## Status
Design Ops handoff artifacts: **not validated** in Figma until designers complete import + Design QA.  
Engineering readiness: **production no-go** (ga-engineering-audit). Do not claim Production GO from this folder.
