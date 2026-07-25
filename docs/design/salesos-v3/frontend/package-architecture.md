# Frontend Package Architecture

```text
salesos/frontend/
  packages/
    design-system/     # primitives + tokens re-export
    icons/
    charts/
    widgets/           # Widget SDK runtime
    hooks/
    layouts/           # shell layouts
    providers/         # theme, workspace, AI preview
    theme/
    tokens/
  src/app/(v3)/        # new route group — do not restyle legacy (dashboard)
```

## Rules

- No legacy `(dashboard)` restyle.
- Feature flag `salesos_v3_shell`.
- Import only from `@salesos/design-system` in `/v3` routes.
- Spike lives at `salesos/frontend/src/app/v3/` (path `/v3`), not a conflicting route group.
