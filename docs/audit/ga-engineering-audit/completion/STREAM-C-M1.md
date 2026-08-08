# Stream C — M1 Quality Gates

**Stream:** C (Quality Gates)  
**Date:** 2026-08-08  
**Charter:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Milestone:** M0 verify + M1 FE lint batch  
**Commit:** **not created** (per order)

---

## 1. Boot / import verify (CP-C-01)

**Prior code fix (Director):** stacked FastAPI path decorators in `salesos/backend/app/main.py`:

```python
@app.get("/api/v1/version", response_model=VersionResponse)
@app.get("/version", response_model=VersionResponse)
```

**Command (Docker; compose backend healthy):**

```text
docker compose exec -T backend python -c "from app.main import app; print('IMPORT_OK', type(app).__name__); paths=[getattr(r,'path',None) for r in app.routes]; print('HAS_/version', '/version' in paths); print('HAS_/api/v1/version', '/api/v1/version' in paths)"
```

**Result:**

```text
IMPORT_OK FastAPI
HAS_/version True
HAS_/api/v1/version True
exit_code: 0
```

| Check | Outcome |
|-------|---------|
| `from app.main import app` | **PASS** — no `TypeError` |
| Both `/version` and `/api/v1/version` registered | **PASS** |
| Full pytest suite | **not run** (low-load; import alone sufficient for this gate) |

**Validation:** **light validated** (targeted import smoke in running Docker backend).

**Disposition:** CP-C-01 import path → **Fixed** (code + import evidence).

---

## 2. FE lint reduction batch (CP-C-02 progress)

### Scope honesty

| Claim class | This session |
|-------------|--------------|
| EAB-era residual (~528) | Historical board figure — **not** re-counted as full-tree |
| Wave 25 cite (531→0) | Cited elsewhere; **not** re-claimed as full CI green here |
| `src/app` + `src/components` | `next lint` → **0** errors (spot) |
| `packages/` before batch | ~**78** `Error:` lines (`next lint --dir packages`) |
| `packages/` after batch | ~**44** `Error:` lines |
| Batch files touched | **11** — all **0** errors on re-lint |
| Full `npm run lint` / CI `lint-frontend` | **may still fail** — residual in `packages/` |
| Full `npm run build` | **not run** |

**CI honesty:** This batch is **progress**, not a green FE lint gate claim. CI job `lint-frontend` (`npm run lint` in `.github/workflows/ci.yml`) can still fail while `packages/` residuals remain.

### Files touched (safe unused-import / typing)

| File | Fixes |
|------|--------|
| `packages/workspace/src/ai-operating-assistant.tsx` | Remove unused lucide + `AI_ACTIONS` imports; `_i`; drop `as any` on textarea ref |
| `packages/workspace/src/generator.ts` | Remove unused type imports |
| `packages/workspace/src/renderer.tsx` | Remove unused hooks/icons; `_entityType` / `_entityId` |
| `packages/workspace/src/revenue-command-center.tsx` | Remove unused imports |
| `packages/workspace/src/universal-inbox.tsx` | Remove unused lucide imports |
| `packages/workspace/src/workspace-types.ts` | Remove unused `WidgetStatus` import |
| `packages/workspace/src/testing/types.ts` | Remove unused `WidgetFeatureFlag` |
| `packages/widget-sdk/src/testing/types.ts` | Remove unused `WidgetFeatureFlag` |
| `packages/design-language/src/elevation.ts` | Remove unused `SHADOW_COLOR` |
| `packages/forms/src/index.tsx` | Remove unused imports; `DefaultValues<T>` instead of `any` |
| `packages/hooks/src/use-command.ts` | Remove unused `useRuntime`; `const globalListeners` |

**Skipped intentionally:** `react-hooks/exhaustive-deps` / `rules-of-hooks` in class/runtime helpers (behavior-risk); no eslint-disable spam; no install; no full build.

**Commands run:**

```text
npx next lint --dir src/components   # 0
npx next lint --dir src/app          # 0
npx next lint --dir packages         # fail; ~78 → ~44 Error lines after batch
npx next lint --file <11 batch files> # 0
```

**Validation:** **light validated** (targeted `next lint` on batch + packages dir count). **not** build validated for full FE gate.

**Disposition:** CP-C-02 → **Partial** (meaningful packages reduction; CI gate not green).

---

## 3. Walls / residuals

| Wall / residual | Status |
|-----------------|--------|
| FE packages lint residual (~44 errors) | Open — next Stream C batch |
| Full `npm run lint` CI honesty | Gate may fail until packages cleared |
| Full pytest / `npm run build` | Deferred (low-load; not required for import prove) |
| npm install | Not needed — `node_modules` present |
| Docker backend | Available — import verified in-container |

---

## 4. Return summary (Director harvest)

| Item | Value |
|------|--------|
| Import | **PASS** (`IMPORT_OK FastAPI`) |
| FE files touched | 11 under `salesos/frontend/packages/` |
| Validation labels | Import: **light validated**; FE batch: **light validated**; CI lint: **not claimed green** |
| Walls | packages ~44 ESLint errors remain; no Blocked-Wall for this stream |

---

*Stream C M1 — 2026-08-08 — AI assists. Humans decide. Evidence governs. — no commit*
