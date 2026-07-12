# @salesos/design-language

MUHIDE design tokens — the single source of truth for visual identity across all SalesOS surfaces.

## Purpose

Defines colors, typography, spacing, elevation, animation, accessibility tokens, and component presets. Used by `@salesos/ui`, `tailwind.config.ts`, and global CSS.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `color` | `color.ts` | MUHIDE palette (brand, semantic, neutral scales) |
| `typography` | `typography.ts` | Font families (Viga, IBM Plex Sans/Arabic/Mono), sizes, weights |
| `spacing` | `spacing.ts` | Spacing scale (4px base) |
| `elevation` | `elevation.ts` | Shadow tokens for depth |
| `animation` | `animation.ts` | Transition and animation tokens |
| `motion` | `motion.ts` | Reduced motion preferences |
| `layout` | `layout.ts` | Layout primitives (Stack, Grid, Section) |
| `components` | `components.ts` | Component preset tokens |
| `states` | `states.ts` | State tokens (hover, active, disabled, focus) |
| `accessibility` | `accessibility.ts` | WCAG AA contrast ratios, focus rings |
| `ai` | `ai.ts` | AI-related tokens |
| `timeline` | `timeline.ts` | Timeline-specific tokens |
| `workspace` | `workspace.ts` | Workspace layout tokens |
| `search-commands` | `search-commands.ts` | Search command tokens |
| `principles` | `principles.ts` | Design principles |

## Usage

```tsx
import { color, typography, spacing } from '@salesos/design-language'

const style = {
  backgroundColor: color.brand.primary,
  fontFamily: typography.fontFamily.sans,
  padding: spacing[4], // 16px
}
```
