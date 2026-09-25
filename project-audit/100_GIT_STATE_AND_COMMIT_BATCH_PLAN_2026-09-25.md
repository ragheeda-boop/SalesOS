# 100 — Git state, secrets in history, and commit batch plan (2026-09-25)

## Purpose

This is decision B9.1 (report 99): prepare commit batches for PO review.
**Nothing was committed, staged or pushed.** The only file changed is
`.gitignore` (§3), and that change is protective and reversible.

## 1. Measured state (branch `fix/login-and-keys`, HEAD `951a86f1`)

| measure | value |
|---|---|
| `git status --porcelain --ignore-submodules=all` | 276 modified · 25 deleted · 439 untracked (was 902 before §3's ignores) |
| staged | 0 |
| Alembic migrations on disk / tracked | **129 / 99** — 30 untracked |
| migration head on disk | `f2e3d4c5b6a7` |
| **migration head reachable from git** | **`h2i3j4k5l6m8` (Phase 4A, 2026-08-23)** |
| `app/modules/master_data/**` (Phases 0–7) | **entirely untracked** |
| `app/modules/entity_resolution/er_router.py`, `signal_actions/{actions,hitl_*}.py`, `effectiveness/**` | untracked |

### Consequence (highest priority)

About a month of work exists only on this local disk:

- Master Data Phases 0–7 and entity resolution.
- The fact ledger, provider spend, DEC-157 RLS and the DLQ fix.
- Every bug fix and test in reports 57–98.

Two risks follow:
- **A deploy built from git would run schema head `h2i3j4k5l6m8`** and
  miss 30 migrations, including RLS closures.
- **A disk failure would lose all of it.** Note that `D:` is a nearly full
  FAT32 volume (report 61).

## 2. Secret found in pushed git history — needs owner action

| path | history | content (inspected without printing) | current app accepts it? |
|---|---|---|---|
| `salesos/infra/monitoring/prometheus-token` | added `3de118a5` (2026-07-15), removed `1cc6c622` (2026-07-26); **the commit is on remote branches (pushed to GitHub)** | 331-char **HS256 JWT**: `type=access`, claims `sub`, `tenant_id`, `aud`, `iss`, `jti`, `kid`; **expires 2036-07-11** | **No.** Live auth verifies RS256 only (`identity/jwks.py`). The HS256 `sdk.security.decode_jwt` has no caller in the app. |
| `salesos/infra/k8s/secrets.yaml` | added `790552d5`, removed `a6834624` | 9-line template with placeholders | n/a |

**Assessment:** the token is not usable against the current code. It must
still be treated as compromised. It reveals its signing algorithm and its
tenant and user identifiers. If the HS256 secret that signed it
(`JWT_SECRET_KEY` of July 2026) is reused anywhere, that secret is exposed
too.

**Recommended owner actions** (not taken here; each is shared-state or
destructive):
1. Rotate any secret that was the HS256 signing key in July 2026, if it is
   still in use (`JWT_SECRET_KEY` / `SECRET_KEY` in Railway, Vercel and CI).
2. Decide whether to purge the blob from history (`git filter-repo`). That
   is a force-push rewriting shared history, and every clone would need to
   re-clone. Rotation alone is usually sufficient when the key is no longer
   accepted.
3. Enable GitHub secret scanning / push protection on the repository.

## 3. `.gitignore` hardening (done)

Added to the root `.gitignore`:
- `salesos/infra/k8s/secrets.yaml` and
  `salesos/infra/monitoring/prometheus-token`. Both are currently untracked
  local files: a 43-byte token with no placeholder, and a Kubernetes
  `Secret`. A broad `git add` would have committed them.
- Generated artifacts: `benchmarks/results/` (460 files),
  `node_modules.incomplete-*`, table-count TSVs, `salesos_test_export/*.dump`.

Verified with `git check-ignore`.

## 4. Proposed commit batches (for review — not executed)

Commit in this order. Each batch should be reviewed with `git diff` before
staging, and staged with **explicit paths only**, never `git add -A`
(AGENTS.md §41).

| # | batch | contents | notes |
|---|---|---|---|
| 1 | `.gitignore` | §3 | Commit first, so later batches cannot sweep in secrets |
| 2 | **Migrations** | the 30 untracked `app/alembic/versions/*.py` plus modified `app/alembic/lib/rls.py` | Must land together: the chain `h2i3j4k5l6m8 → … → f2e3d4c5b6a7` is only valid complete. Verified single head on disk. |
| 3 | **Master Data platform** | `app/modules/master_data/**`, `app/modules/entity_resolution/**`, `scripts/{muhide_*,_muhide_global_ids,fix_false_cr,phase6_*,phase7a_*,stage_master_contacts_v07}.py` | Built across many sessions (§34–§100). Review as a unit. |
| 4 | **Runtime / domain / intelligence fixes** | the modified files under `runtime/`, `domains/`, `intelligence/`, `sdk/events/`, `app/modules/{company,signal_actions,cache,communication_hub,identity}`, `app/boot/startup.py`, `app/config.py` | These diffs **mix changes from parallel sessions**. Review each hunk against reports 57–98. |
| 5 | **Tests** | untracked `tests/unit` (76) + `tests/integration` (61), plus modified tests | Depends on batches 2–4. |
| 6 | **Frontend** | untracked `frontend/src/app` (26), `src/lib` (17), `src/features`, `src/components`, `scripts/sync-to-c-and-verify.ps1`, plus modified files | Built in the C: mirror (report 61). Run typecheck/build before committing. |
| 7 | **Docs** | `project-audit/57–100`, `docs/program/decisions/DEC-157..159`, `DECISION_LOG.md`, `AGENTS.md`, `AUDIT_INVENTORY.md` | |
| — | **25 deletions** | the unstaged `D` entries (stale root markers, per AGENTS.md §41) | A separate, explicit decision: confirm, then `git rm` by name. |

### Deliberately excluded

- `salesos_test_export/muhide_global_id_pins_20260920.csv.gz` (10 MB).
  **Recommendation:** keep it next to the dump it was derived from, with an
  off-disk backup, rather than in git. If it must be versioned, use Git LFS.
  The restore scripts refuse to run without it (report 96).
- The secrets and generated artifacts in §3.

## 5. Recommendation

Execute batches 1–2 **soon**. They are small, and they remove the two
largest risks: a secret being committed, and the deployable schema
diverging from the code. Batches 3–7 need a human review pass, because
they carry weeks of parallel-session work.

## Deliberate non-claims

- No commit, stage, push, history rewrite or secret rotation was
  performed. Only `.gitignore` changed.
- File classification was built from the paths named in reports 67–99 plus
  `git status`. Batch 4's mixed-session diffs were not reviewed hunk by
  hunk here.
- Whether the July HS256 signing secret is still deployed anywhere was
  **not** verified. No production or Railway access was used.
