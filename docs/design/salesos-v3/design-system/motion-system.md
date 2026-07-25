# Motion System

## Tokens

| Token | Default | Use |
|-------|---------|-----|
| `--duration-instant` | 0–50ms | Opacity toggles |
| `--duration-fast` | 120ms | Hover |
| `--duration-normal` | 200ms | Panels |
| `--duration-slow` | 320ms | Page transition |
| `--ease-standard` | cubic-bezier(0.2,0,0,1) | UI |
| `--ease-emphasize` | cubic-bezier(0.2,0,0,1) | Entrances |

## Patterns

Hover · Focus ring · Expand/Collapse · Drag/Drop · Sheet enter/exit · Skeleton shimmer · Shared-element optional · Page transition fade+slide 8px.

## Reduced motion

If `prefers-reduced-motion: reduce` → durations → 0; keep opacity only.
