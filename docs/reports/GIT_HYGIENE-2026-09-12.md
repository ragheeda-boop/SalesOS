# Git Hygiene — 2026-09-12

**Agent:** A1 — Git Safety / Hygiene  
**Branch:** `fix/login-and-keys`  
**Workspace:** `D:\AISalesOS`  
**Validation:** **service-grade** (commands run; outcomes recorded; no overclaim)  
**Production GO:** not claimed. No PRs merged. Index not re-mutated after Phase 0.

---

## 1. Phase 0 — Index unpoison (FACT)

### Commands run

```powershell
# cwd: D:\AISalesOS
git reset HEAD -- .
git status
git diff --cached --stat
```

Follow-ups used only because plain `git status` failed on a broken submodule (read-only; no index mutation):

```powershell
git status --ignore-submodules
git diff --cached --name-status
git diff --cached --name-only | Measure-Object -Line
```

### `git reset HEAD -- .`

- **Exit code:** 0
- **Elapsed:** ~67.5 s (hint: “It took 60.57 seconds to refresh the index after reset.”)
- **Effect:** unstaged the poisoned index (~4,748 staged deletions). Working tree was **not** reset, restored, or deleted by this command.
- **Forbidden commands not used:** `git add`, `git commit`, `git push`, `git merge`, `git rebase`, `git reset --hard`, discarding `checkout`, `git clean -fd`, force-push, `git config`, `--amend`.

### `git diff --cached` after reset

- **`git diff --cached --stat`:** empty (no output)
- **Staged file count:** **0**
- **Staged deletions (“D” in index):** **0**

Acceptance met: cached/index is empty.

### `git status` after reset

**Plain `git status` (exact outcome):**

```
fatal: not a git repository: engineering-os/../.git/modules/engineering-os
```

Exit code 128. Caused by a broken `engineering-os` submodule pointer (`.git/modules/engineering-os` missing / invalid). This is a leftover risk, not an index-poison symptom.

**`git status --ignore-submodules` (exact outcome):**

```
On branch fix/login-and-keys
Changes not staged for commit:
  ...
	modified:   .gitignore
	deleted:    REPO_TOPOLOGY_AUDIT.md
	... (pre-existing unstaged working-tree D/M only) ...
	deleted:    salesos/start.sh

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	... (large untracked set; benchmarks, modules, project-audit, etc.) ...

no changes added to commit (use "git add" and/or "git commit -a")
```

**FACT:** after reset, **zero staged deletions**. All `deleted:` / `modified:` lines were **unstaged working-tree** changes that already existed on disk. `git reset HEAD -- .` did not add, restore, or remove those files.

Pre-existing unstaged working-tree deletions observed (not created by this agent; **not** staged):

| Path (examples) | Column |
|---|---|
| `REPO_TOPOLOGY_AUDIT.md` | unstaged `D` |
| `get-docker.sh` | unstaged `D` |
| `salesos/.editorconfig`, `salesos/.gitignore`, `salesos/README.md`, `salesos/start.sh`, … | unstaged `D` |
| `salesos/backend/app/...` (company, identity, routers, tests) | unstaged `M` |
| `salesos/frontend/src/...` (login, companies, nav) | unstaged `M` |

These remain **dangerous if anyone later runs `git add -A`**. They are **not** in the index now.

---

## 2. Files deleted (disk only; no `git add` / `git rm`)

Verified contents before delete. Root-level copies of the named junk files: **UNKNOWN / not found**.

| Path | Verdict | Action |
|---|---|---|
| `salesos/backend/orphan_dump.txt` | Junk dump (account row text; email/phone). Untracked. | **DELETED** |
| `salesos/backend/test_reg.py` | Ad-hoc localhost register probe (prints access token). **Was tracked.** | **DELETED** (disk). Now unstaged `D`. |
| `salesos/backend/test_store.py` | Ad-hoc event-store INSERT probe. **Was tracked.** | **DELETED** (disk). Now unstaged `D`. |
| `salesos/backend/direct_import.py` | One-off import; hardcoded tenant + DB URL. Untracked. | **DELETED** |
| `salesos/scripts/direct_import.py` | Same junk script as above. **Was tracked.** | **DELETED** (disk). Now unstaged `D`. |
| `salesos/backend/celerybeat-schedule` | Celery beat local state (binary). Untracked. | **DELETED** |
| `salesos/backend/.tmp-runs-tip8.json` | Obvious tmp (GitHub Actions run dump). Untracked. | **DELETED** |
| `orphan_dump.txt` (repo root) | Not found | **UNKNOWN** |
| `test_reg.py` (repo root) | Not found | **UNKNOWN** |
| `test_store.py` (repo root) | Not found | **UNKNOWN** |
| `direct_import.py` (repo root) | Not found | **UNKNOWN** |
| `celerybeat-schedule` (repo root) | Not found | **UNKNOWN** |
| `.tmp-*` (repo root) | Not found | **UNKNOWN** |

**Not deleted (ignore only):** 14 `.mypy_cache_*` directories and `salesos/backend/.venv/` (local caches / venv; not product).

---

## 3. `.gitignore` diffs

### Root `D:\AISalesOS\.gitignore`

**This session added** (under `# Python`):

```
# Mypy incremental caches (local/CI variant dirs — never commit)
.mypy_cache/
.mypy_cache_*
```

**Why:** 14 on-disk variants under `salesos/backend/` were **not** ignored (`git check-ignore` had no match before the edit). Pattern covers all current and future `.mypy_cache_*` dirs.

**Already present (unchanged by this session’s intent):** `.venv/` (root line 7) — already ignored `salesos/backend/.venv`.

**Pre-existing unstaged addition already in the working-tree file after Phase 0 (not introduced by A1 logic; left in place):**

```
salesos/backend/outputs/
```

### New `D:\AISalesOS\salesos\backend\.gitignore`

File did **not** exist. Created with:

| Pattern | Why |
|---|---|
| `.venv/` | Belt-and-suspenders; backend venv must never be presented for commit |
| `.mypy_cache/` and `.mypy_cache_*` | All 14 local/CI mypy cache dirs |
| `celerybeat-schedule` / `celerybeat-schedule.*` | Celery local state |
| `orphan_dump.txt`, `test_reg.py`, `test_store.py`, `direct_import.py` | Named junk so it cannot be re-added casually |
| `.tmp-*` / `.tmp_*` | Obvious tmp dumps |

### Ignore proof (after edit)

`git check-ignore -v` matched **all 14** mypy dirs + `.venv` + celerybeat + orphan_dump + `.tmp-runs-tip8.json`.

Observed mypy dirs (all ignored):

`.mypy_cache_ci20`, `.mypy_cache_final`, `.mypy_cache_p14`, `.mypy_cache_p14b`, `.mypy_cache_p17`, `.mypy_cache_p17b`, `.mypy_cache_p17c`, `.mypy_cache_p17d`, `.mypy_cache_p19`, `.mypy_cache_p20`, `.mypy_cache_p20c`, `.mypy_cache_p20d`, `.mypy_cache_phase11`, `.mypy_cache_phase12`.

### Confirmation: 0 new temp files tracked; `.venv` will not be presented for commit

| Check | Result |
|---|---|
| `git ls-files` on `.venv`, `.mypy_cache_*`, `celerybeat-schedule`, `orphan_dump.txt`, backend `direct_import.py`, `.tmp-runs-tip8.json` | **empty** — none tracked |
| `git check-ignore` on `salesos/backend/.venv` | **ignored** (`.gitignore` / backend `.gitignore`) |
| `git diff --cached` | **empty** — this session staged nothing |
| New temp files added to the index | **0** |

---

## 4. Dependabot classification

**Sources (read-only):**

- Active config: `.github/dependabot.yml` (canonical; weekly Monday; ecosystems: npm `/salesos/frontend`, pip `/salesos/backend`, docker backend, docker frontend, github-actions `/`)
- Duplicate/inert: `.github/.github/dependabot.yml` (same content; untracked nested copy; GitHub does **not** load this path)
- Open PRs: `gh pr list --search "author:app/dependabot"` — **27 open**. None merged. No application code edited.

**Local constraint evidence:**

- Backend: `fastapi >=0.136,<0.142`; `pydantic >=2.9,<3`; `pydantic-settings >=2.2,<2.5`; `bcrypt >=4.0,<4.1`; `uvicorn ^0.29`; Docker `FROM python:3.12-slim`
- Frontend: `react ^19.0`; `next ^15.0`; Docker `FROM node:22-alpine`

**Do not merge any of these without a dedicated owner.** Classification is advisory only.

### SAFE

Low blast radius (patch / font / test-only / scanner pin). Still requires CI green; **not merged**.

| PR | Title / bump | Evidence |
|---|---|---|
| [#19](https://github.com/ragheeda-boop/SalesOS/pull/19) | `@fontsource/ibm-plex-sans` 5.2.8 → 5.3.0 | Font file only |
| [#17](https://github.com/ragheeda-boop/SalesOS/pull/17) | `autoprefixer` 10.5.2 → 10.5.4 | Patch, CSS build-time |
| [#18](https://github.com/ragheeda-boop/SalesOS/pull/18) | `@playwright/test` 1.61.1 → 1.62.0 | Dev e2e runner, minor |
| [#14](https://github.com/ragheeda-boop/SalesOS/pull/14) | frontend testing group (3) | `dependabot.yml` testing group; not runtime |
| [#36](https://github.com/ragheeda-boop/SalesOS/pull/36) | backend testing group (4) | pytest/coverage group; not runtime |
| [#4](https://github.com/ragheeda-boop/SalesOS/pull/4) | `aquasecurity/trivy-action` SHA pin | Scanner action hash only |

### SECONDARY

Needs human review. Not a language/runtime major, but can break CI, lint, or UI contracts.

| PR | Title / bump | Evidence |
|---|---|---|
| [#32](https://github.com/ragheeda-boop/SalesOS/pull/32) | react group: react/react-dom 19.2.7→19.2.8; types patches; `react-hook-form` 7.81.0→7.87.0 | Runtime UI; hook-form **minor** |
| [#10](https://github.com/ragheeda-boop/SalesOS/pull/10) | radix group (8 updates) | Shared primitives; visual/a11y risk |
| [#24](https://github.com/ragheeda-boop/SalesOS/pull/24) | `httpx` 0.27.2 → 0.28.1 | HTTP client minor; used in identity/probes |
| [#31](https://github.com/ragheeda-boop/SalesOS/pull/31) | `ruff` 0.11.13 → 0.16.3 | Dev linter; large rule churn |
| [#20](https://github.com/ragheeda-boop/SalesOS/pull/20) | `mypy` 1.20.2 → 2.3.1 | Dev-only but **mypy 2 major** |
| [#1](https://github.com/ragheeda-boop/SalesOS/pull/1) | `actions/cache` 4.3.0 → 6.1.0 | CI-only; major action API |
| [#2](https://github.com/ragheeda-boop/SalesOS/pull/2) | `actions/download-artifact` 4.3.0 → 8.0.1 | CI-only; major action API |
| [#7](https://github.com/ragheeda-boop/SalesOS/pull/7) | `actions/checkout` 4.2.2 → 7.0.1 | CI-only; major action API |
| [#8](https://github.com/ragheeda-boop/SalesOS/pull/8) | `actions/upload-artifact` 4.6.2 → 7.0.1 | CI-only; major action API |

### MAJOR

Do not merge. Crosses language, framework, pin floors, or major package versions.

| PR | Title / bump | Evidence |
|---|---|---|
| [#37](https://github.com/ragheeda-boop/SalesOS/pull/37) | fastapi group: `uvicorn` 0.29.0→0.52.4; pydantic + `pydantic-settings` (→2.15.0 in body) | `uvicorn ^0.29` is `<0.30`; `pydantic-settings` pin is `<2.5`. Exceeds local floors. ASGI/settings behavior. |
| [#35](https://github.com/ragheeda-boop/SalesOS/pull/35) | `aiokafka` 0.10.0 → 0.14.0 | Event bus client, multi-minor |
| [#34](https://github.com/ragheeda-boop/SalesOS/pull/34) | `redis` 5.3.1 → 8.1.0 | **Major** client; OAuth/state store |
| [#33](https://github.com/ragheeda-boop/SalesOS/pull/33) | `openai` 1.109.1 → 3.2.0 | **Two majors**; AI provider path |
| [#28](https://github.com/ragheeda-boop/SalesOS/pull/28) | `bcrypt` 4.0.1 → 5.0.0 | **Major**; `pyproject` pins `>=4.0,<4.1` (auth hashes) |
| [#27](https://github.com/ragheeda-boop/SalesOS/pull/27) | neo4j `^5.20` → `>=5.20,<7.0` | Widens to 6.x |
| [#21](https://github.com/ragheeda-boop/SalesOS/pull/21) | `@hookform/resolvers` 3.10.0 → 5.5.7 | **Major skip** (v4 unused) |
| [#16](https://github.com/ragheeda-boop/SalesOS/pull/16) | `recharts` 2.15.4 → 3.10.1 | Charts **major** |
| [#15](https://github.com/ragheeda-boop/SalesOS/pull/15) | `lucide-react` 0.460.0 → 1.27.0 | Icons **major** |
| [#13](https://github.com/ragheeda-boop/SalesOS/pull/13) | `eslint-config-next` 15.5.22 → 16.2.12 | Next 16 eslint vs app on Next 15 |
| [#5](https://github.com/ragheeda-boop/SalesOS/pull/5) | Docker `python` 3.12-slim-bookworm → **3.14**-slim-bookworm | Language major; `pyproject` is `^3.12` |
| [#3](https://github.com/ragheeda-boop/SalesOS/pull/3) | Docker `node` 22-alpine → **25**-alpine | Node major vs current 22 |

---

## 5. Validation status

| Item | Status |
|---|---|
| Index unpoisoned (0 staged / 0 cached) | **PASS** — `git diff --cached` empty |
| Working tree not hard-reset | **PASS** — only `git reset HEAD -- .` |
| Junk deleted after content verify | **PASS** — 7 paths deleted; root names UNKNOWN |
| `.mypy_cache_*` + `.venv/` ignored | **PASS** — `git check-ignore` on all 14 + venv |
| 0 new temp files tracked | **PASS** |
| Dependabot PRs merged | **NONE** (classified only) |
| App / railway / config / tests / AGENTS / audit docs | **UNTOUCHED** |
| Full npm / pytest / install | **NOT RUN** (low-load) |

**Label:** service-grade (command evidence). Not “light”. Not production-ready. Not a GO.

---

## 6. Files changed (this agent)

| Path | Change |
|---|---|
| `D:\AISalesOS\.gitignore` | Added `.mypy_cache/` + `.mypy_cache_*` |
| `D:\AISalesOS\salesos\backend\.gitignore` | **Created** (venv / mypy / celery / junk / tmp) |
| `D:\AISalesOS\docs\reports\GIT_HYGIENE-2026-09-12.md` | **Created** (this report) |
| `salesos/backend/orphan_dump.txt` | Deleted (untracked junk) |
| `salesos/backend/test_reg.py` | Deleted (tracked junk → unstaged `D`) |
| `salesos/backend/test_store.py` | Deleted (tracked junk → unstaged `D`) |
| `salesos/backend/direct_import.py` | Deleted (untracked junk) |
| `salesos/scripts/direct_import.py` | Deleted (tracked junk → unstaged `D`) |
| `salesos/backend/celerybeat-schedule` | Deleted (untracked junk) |
| `salesos/backend/.tmp-runs-tip8.json` | Deleted (untracked tmp) |

**Index:** unchanged after Phase 0. Nothing staged.

---

## 7. Leftover risks (not fixed here)

1. **Broken `engineering-os` submodule** — plain `git status` fatals. Needs submodule repair by an owner; do not `checkout`/`clean` blindly.
2. **`git add -A` is still unsafe** — large unstaged `D`/`M` set plus huge untracked tree (benchmarks JSON, modules, `project-audit/`, `salesos/backend/app/modules/identity/_keys/`). Staging everything would re-poison the index or commit secrets/junk.
3. **Three tracked junk deletions are unstaged** (`test_reg.py`, `test_store.py`, `salesos/scripts/direct_import.py`). A later authorized `git add` of those paths would record the deletes; do not `git checkout --` them.
4. **27 open Dependabot PRs** — several **MAJOR** (Python 3.14, Node 25, redis 8, openai 3, bcrypt 5, uvicorn 0.52 vs `^0.29`). Do not batch-merge.
5. **Duplicate** `.github/.github/dependabot.yml` — inert untracked copy; safe to ignore or delete in a later hygiene pass.
6. **`salesos/.gitignore` already missing on disk** (pre-existing unstaged `D`) — product ignore file; **not restored** (would require checkout). Backend ignore now exists as a local backstop.

---

*A1 complete. Index first. No commit. No push. No Dependabot merge.*
