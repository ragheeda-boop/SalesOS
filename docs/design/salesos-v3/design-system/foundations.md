# Design System V3 — Foundations

## Direction

Cool neutral canvas, restrained accent (brand orange `#F57C1E` retained as primary CTA only), semantic status colors, display type for homes + UI sans for data, **4px** spacing grid, 5 elevations, light + dark.

## Typography

| Token | Size | Use |
|-------|------|-----|
| display | 32–40 | Home titles |
| title | 20–24 | Page h1 |
| subtitle | 16–18 | Section |
| body | 14 | Default |
| meta | 12 | Tables, hints |

Line-height pairs documented in code tokens later. Avoid Inter-as-default-only; prefer existing MUHIDE font stack unless Design Ops selects new licensed faces.

## Spacing

`--space-1`…`--space-16` on 4px grid (4–64).

## Color

Primitives + semantic: `--text-*`, `--bg-*`, `--surface-*`, `--border-*`, `--status-*`, `--ai-*` (AI surfaces distinct). Muted text **≥ 4.5:1**.

## Radius / Elevation

Radius: sm/md/lg/pill. Elevation: sm/md/lg/xl/focus-ring.

## Theme

Class-based `.dark`. Charts use brand-aligned palette (no random blue-first).

## Grid

App: sidebar + main. Content: 12-col at xl. Dashboards: 12-col widget grid.
