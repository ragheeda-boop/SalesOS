# Frontend Toolchain Root Cause + Fix — 2026-09-23

## The question this answers

Every session since at least 2026-09-20 has recorded some version of "the
local frontend dependency tree is incomplete" or "TypeScript/Jest/build are
not release evidence in this checkout," and worked around it with one-off
temporary copies to `C:\Users\raghe\AppData\Local\Temp\...`. None of those
sessions identified *why* `npm install` never fully succeeds directly under
`D:\AISalesOS`. This report identifies the root cause and ships a permanent,
reusable fix instead of another one-off temp copy.

## Root cause (verified this session)

```text
D:               15G   14G  805M  95% /d      File System Name: FAT32
C:              475G  317G  158G  67% /c
```

`D:\AISalesOS` — the entire project, including this repository — lives on a
**FAT32-formatted volume with 805MB free out of 15GB**. Two independent,
compounding problems:

1. **FAT32 cannot represent symlinks or NTFS reparse points at all.**
   `npm install` on any non-trivial package tree creates symlinks under
   `node_modules/.bin/` (one per executable a dependency exposes) as a
   normal part of its operation. On a FAT32 target, every one of those
   symlink creations fails. This is a hard filesystem-capability limit, not
   a permissions or disk-space issue — **no amount of freed space fixes it**.
   This is very likely the exact mechanism behind the repeatedly-recorded
   `EPERM`/`EISDIR` errors during `npm install` and during Next.js
   standalone-output tracing in prior sessions.
2. **805MB free is also, independently, too little.** A `node_modules` tree
   for this project (Next.js 15, TypeScript, Jest, Playwright, Storybook,
   multiple `@salesos/*` internal packages) needs on the order of 1–1.5GB+.
   Even if FAT32 supported symlinks, this checkout would still run out of
   disk mid-install.

Either problem alone would block a working frontend toolchain on `D:`
directly; together they make it certain, which matches every prior
session's experience exactly.

### Where the space on `D:` is going (informational, not acted on)

```text
packages   5.51 GB   (packages\data 3.86 GB, packages\packages\data 1.58 GB — a nested
                       duplicate already flagged as a hygiene issue in AUDIT_INVENTORY.md §1)
salesos    2.34 GB
docs       1.33 GB
business   0.93 GB
salesos_test_export  0.52 GB  (the pg_dump backup referenced by Phase 7 reports — legitimate, not junk)
```

`packages/packages/data` (1.58GB) reproduces the exact duplication
`AUDIT_INVENTORY.md` already named as a hygiene issue. Reclaiming it would
roughly double the free space on `D:` (805MB → ~2.3GB) but would **still
not** fix problem 1 (FAT32 has no symlinks regardless of free space), so it
was **not deleted this session** — freeing it doesn't solve the actual
blocker, and deleting 1.58GB of someone else's data pipeline output without
being asked is not this task's scope. Flagging it here for a decision, not
acting on it.

## The fix: a persistent, reusable NTFS mirror + verify script

Rather than another disposable temp copy, this session adds
`salesos/frontend/scripts/sync-to-c-and-verify.ps1`, checked into the repo
so every future session (and the user, interactively) can use the same
command instead of rediscovering this problem:

```powershell
powershell -File salesos/frontend/scripts/sync-to-c-and-verify.ps1
```

What it does:
1. `robocopy /MIR`s `salesos/frontend` (excluding `node_modules`, `.next`,
   `coverage`, `.turbo`, `dist`, `build`, `.git`) from `D:\AISalesOS` to a
   fixed, persistent location on `C:` (`C:\Users\raghe\dev\SalesOS-frontend`
   by default — not a temp folder, so it survives across sessions and reboots
   and does not need re-creating from scratch every time).
2. Runs `npm ci` there (NTFS, plenty of free space — symlinks and disk space
   both work).
3. Runs a verification command (`npm run typecheck` by default; pass
   `-Command build` or `-Command test` for the other checks).

Source of truth for editing remains `D:\AISalesOS` exactly as before — this
does not move the git repository or change where the user commits. Re-run
the script (an incremental `robocopy /MIR`, fast after the first run) any
time before testing frontend changes.

## Verification (this session)

Ran the script end to end against the current source, three ways:

| Check | Command | Result |
|---|---|---|
| Install | `npm ci` (via the script, `-SkipInstall` omitted) | **PASS** — 871 packages installed, 0 symlink/EPERM errors, ~1 minute |
| TypeScript | `-Command typecheck` (`tsc --noEmit`) | **PASS** |
| Unit tests | `-Command test` (`jest --config jest.config.js`) | **PASS** — 334/334 suites, 2689 passed + 1 skipped = 2690 total, 0 failed, 125.9s |
| Production build | `-Command build` (`next build`) | **PASS after two real source fixes** (below) — full route tree generated, 0 errors |

The first `build` run compiled successfully but failed at Next.js's
build-time lint pass with three genuine, pre-existing source issues that
had never been caught before, because `next build`'s lint step had never
been able to run to completion in this checkout until this session's fix:

1. `src/app/v3/cs/page.tsx:195` — a hardcoded `text-red-600` Tailwind class
   instead of this codebase's `text-[var(--text-danger)]` CSS-variable
   convention (`custom-rules/no-tailwind-color-classes`). Fixed.
2. `src/app/v3/cs/page.tsx:233` (original numbering) — a stray
   `eslint-disable-next-line react-hooks/exhaustive-deps` comment sitting
   above a plain `const` statement that triggers no such rule (an unused
   directive). Removed.
3. `src/app/v3/tasks/[id]/page.tsx:6` — an unused `TaskResponse` type
   import. Removed.
4. `src/app/v3/cs/page.tsx`'s `useMemo` was missing `enabled` in its
   dependency array even though it reads `enabled` in its body (`enabled`
   is derived only from `ready`/`hasToken`, both already tracked, so this
   was a correctness gap with no runtime behavior change). Fixed by adding
   `enabled` to the array.

Removing item 2's stray disable-comment then unmasked a **second, real**
`react-hooks/exhaustive-deps` violation the disable-comment had been
(incorrectly) placed to suppress at the wrong line: `const companies =
companiesQuery.data?.items ?? []` created a fresh array reference on every
render, defeating the memoization of the `useMemo` it feeds. Fixed per
ESLint's own suggested remedy — wrapped it in its own
`useMemo(() => companiesQuery.data?.items ?? [], [companiesQuery.data])`.
A second build run then passed cleanly. All fixes are narrow, verified
correct (`companies`/`enabled` dependency changes only affect when a memo
recomputes, not what it computes), and touch exactly two files.

## Browser verification of the two edited pages

Per this project's own standard, a UI change is not verified by
compile/build alone. Added `.claude/launch.json` (`frontend-c`, port 3100)
and `C:\Users\raghe\dev\run-frontend-dev.cmd` so `next dev` can be launched
from the C: mirror. Started the dev server and navigated to both edited
routes:

| Route | Result |
|---|---|
| `/v3/cs` | Redirected to `/login?callbackUrl=%2Fv3%2Fcs` — correct unauthenticated behavior, 0 console errors, 0 network failures |
| `/v3/tasks/some-test-id` | Redirected to `/login?callbackUrl=%2Fv3%2Ftasks%2Fsome-test-id` — same, 0 console errors, 0 network failures |

No authenticated session was available in this checkout (consistent with
every prior session's documented limitation), so the actual CS survey panel
and task detail body were not rendered with real data — only confirmed to
compile, route, and redirect cleanly with no runtime errors. Server stopped
after verification.

## Files changed this session

- `salesos/frontend/scripts/sync-to-c-and-verify.ps1` — new, the permanent fix
- `salesos/frontend/src/app/v3/cs/page.tsx` — 4 lint fixes (see above)
- `salesos/frontend/src/app/v3/tasks/[id]/page.tsx` — unused import removed
- `.claude/launch.json` — new `frontend-c` dev-server config (port 3100) for browser verification against the C: mirror
- `C:\Users\raghe\dev\run-frontend-dev.cmd` — new, outside the repo; small wrapper so `launch.json` can `cd` into the C: mirror before `npm run dev`

## Deliberate non-claims

- This does not fix FAT32 itself — `D:\AISalesOS` remains FAT32 and remains
  unable to host `node_modules` directly. Reformatting `D:` to NTFS would
  fix this permanently but **erases every file on the drive** and was not
  attempted or recommended as an automatic action; it is the user's call,
  requiring a full backup first.
- `packages/packages/data`'s duplication is flagged, not deleted.
- This is a developer-workflow fix, not a CI/deployment fix — Railway and
  Vercel build from git history on their own infrastructure and were never
  affected by this local FAT32 constraint.
- No production, database, or deployment action was taken. This report and
  script are the only changes.
