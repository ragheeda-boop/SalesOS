# Stream C — W2 FE packages lint batch

**Date:** 2026-08-08  
**Prior:** [STREAM-C-M1.md](./STREAM-C-M1.md)  
**Board:** CP-C-02 Fixed (packages Errors, W5) · CP-C-02b Fixed (cited)

## Result

| Metric | Before W2 | After W2 |
|--------|----------:|---------:|
| `next lint --dir packages` Errors | ~44 | **~9** |
| Batch style | unused import/any/Storybook hook rename | — |
| Full `npm run lint` / build | not run | not run |

## Residual (~9 Errors — skipped at W2)

hooks exhaustive-deps (`use-entity`, `use-utils`); `state-runtime` rules-of-hooks in class; widget-sdk / workspace exhaustive-deps.

## W4 follow-up (WAVE-20260808-4)

Safe exhaustive-deps batch (no disable spam): `use-entity`, `create-widget` (`toast`), `widget-lifecycle` refs, workspace `onReadyRef`.

| Metric | After W2 | After W4 |
|--------|---------:|---------:|
| `next lint --dir packages` Errors | ~9 | **4** |

**Still skipped:** `useKeyboard` spread deps; `state-runtime` class `useStore` rules-of-hooks (3). Full `npm run lint` / build **not run**. Evidence: `completion/evidence/wave-20260808-4/lint-packages.txt`.

## W5 follow-up (WAVE-20260808-5)

Closed remaining packages **Errors** without eslint-disable:

| Metric | After W4 | After W5 |
|--------|---------:|---------:|
| `next lint --dir packages` Errors | 4 | **0** |
| Warnings (a11y date-picker) | 2 | **2** (unchanged; not Errors) |

- `useKeyboard`: handlerRef + `[key]` (dropped unused deps spread; zero in-repo callers)
- `useStore`: extracted function hook `useStore(runtime, path)`; class method removed (rules-of-hooks)

**CP-C-02** → **Fixed** (packages Errors). Full `npm run lint` / build **not run**. Evidence: `completion/evidence/wave-20260808-5/lint-packages.txt`.

## Harvest sync

Wave 25 full-tree lint/build claims stay **Fixed (cited)** on **CP-C-02b** — do not equate with live W5 packages Errors 0 (full `npm run lint` still not re-run).
