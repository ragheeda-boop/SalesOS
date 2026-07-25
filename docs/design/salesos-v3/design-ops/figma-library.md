# Figma Library — SalesOS DS v3

Library file name: **SalesOS DS v3**  
No Figma API in this workspace — import is **manual** (or Tokens Studio / Variables Import plugin) using artifacts in this folder.

## Pages

| Page | Contents |
|------|----------|
| Foundations | Color / type / space / radius specimens from Variables |
| Components | Build per [`figma-component-inventory.md`](./figma-component-inventory.md) |
| Patterns | Data Grid, form layouts, empty/error/permission |
| Dashboards | Widget patterns + Sales Home |
| Templates | Priority frames in [`figma-frames-priority.md`](./figma-frames-priority.md) |

## Modes / themes

- Variables collections: **Color/Light** · **Color/Dark** · **Space** · **Radius** · **Typography** (`tokens.figma.json`)
- App theme: class-based `.dark` — bind Light collection to light frames, Dark to dark frames (or dual-mode aliases after first publish)
- Brand orange `#F57C1E` = primary CTA / border-active only
- Muted text light `#8C8374` (contrast-safe ≥4.5:1)

## Exact import steps (Variables → publish library)

### A. Create the library file

1. In Figma: **New design file** → rename to `SalesOS DS v3`.
2. Create pages: `Foundations`, `Components`, `Patterns`, `Dashboards`, `Templates`.
3. Enable **Variables** (right sidebar → Local variables).

### B. Import / recreate Variables from `tokens.figma.json`

**Option 1 — Plugin (preferred if available)**  
1. Install **Tokens Studio for Figma** or a **Variables Import** plugin that accepts JSON.  
2. Open plugin → Import / Sync → select  
   `docs/design/salesos-v3/design-ops/tokens.figma.json`.  
3. Map collections to Figma collections with these exact names:  
   - `Color/Light` (COLOR)  
   - `Color/Dark` (COLOR)  
   - `Space` (FLOAT, px)  
   - `Radius` (FLOAT, px)  
   - `Typography` (STRING for families; FLOAT for size/weight/line-height)  
4. Confirm modes: each collection has mode `Default` (Light/Dark are **separate collections**, not dual modes).  
5. Resolve any opacity fields (`surface/glass`, etc.) as COLOR with alpha.

**Option 2 — Manual (no plugin)**  
1. Local variables → **Create collection** → name `Color/Light`.  
2. For each key under `collections["Color/Light"].variables` in `tokens.figma.json`, add a COLOR variable (use `/` groups: `text/primary`, `bg/primary`, …).  
3. Repeat for `Color/Dark` (same variable names, dark hex values).  
4. Create collection `Space` — FLOAT variables `space/1`…`space/16`, plus `space/sidebar`, `space/ai-popup`, `space/ai-popup-max-h` (Ask AI modal sizing — not a layout rail).  
5. Create collection `Radius` — FLOAT `radius/sm`…`radius/pill`.  
6. Create collection `Typography` — STRING font families + FLOAT sizes/weights/line-heights.  
7. Create **Text styles**: Display (Viga), Title, Subtitle, Body, Meta — bind sizes to Typography variables.  
8. Create **Effect styles** for elevations listed under `effectStyles` in the JSON (include `elevation/modal`).

### C. Bind and build components

1. On Foundations page, paint swatches bound to Variables (not hard hex).  
2. Build components using names/variants/states from [`figma-component-inventory.md`](./figma-component-inventory.md).  
3. Every interactive component: default · hover · focus · active · disabled · loading · error · success (as applicable).  
4. AI components always include **Preview** Badge.

### D. Build priority frames

1. Follow order in [`figma-frames-priority.md`](./figma-frames-priority.md) / [`FIGMA_BUILD_CHECKLIST.md`](./FIGMA_BUILD_CHECKLIST.md):  
   Login → Shell → Sales Home → Company List → Company 360 → Deal 360 → Data Grid → **Ask AI popup** (modal overlay) → RBAC.  
2. Use library components only (no one-off colors on frames).  
3. Ask AI is **never** a docked rail — draw as scrim + dialog (`space/ai-popup`).  
4. Annotate 18-point notes where needed (see `screens/_TEMPLATE.md`).

### E. Publish library

1. Design Review → DS Approval (see [`review-release.md`](./review-release.md)).  
2. Figma: **Assets** panel → library file → **Publish library** (or Share → Publish).  
3. Publish notes: version + changelog pointer (semver per [`token-code-sync.md`](./token-code-sync.md)).  
4. In product files: **Enable library** → swap any detached styles to library Variables/components.  
5. Branching: `main` = published · `feat/*` = WIP — publish only from approved `main`.

### F. Code sync (after publish)

1. Treat code tokens as eventual SoT; Figma mirrors (`token-code-sync.md`).  
2. Breaking variable renames = semver major + deprecation notice.  
3. CI (when enabled): no raw hex in `src/app/(v3)`.

## Rules

- Components match `design-system/components.md` names.  
- Prefer Sheets over stacked Modals.  
- Do **not** claim Production GO from library publish alone.
