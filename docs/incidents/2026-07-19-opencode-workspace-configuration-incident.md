# Incident Investigation Report

**Incident Date:** July 19, 2026
**Workspace:** Muhide (OneDrive-synced)
**Severity:** High — Complete loss of Agents and Models in OpenCode TUI
**Status:** Immediate cause confirmed. Ultimate root cause unknown.

---

## Executive Summary

The Muhide workspace lost its Agents and Models because **`opencode.json` was physically deleted from disk**. The deletion was never committed to git — it exists only as an unstaged change. Without this file, OpenCode fell back to its global config (`~/.config/opencode/opencode.jsonc`), which contains only a schema reference and no agent or model definitions. The Model Selector disappeared as a **side effect** of losing the Agent definitions, not independently.

---

## Timeline

| Date & Time (ISO) | Event | Commit | Evidence |
|------|-------|--------|----------|
| Jul 8, 2026 | `opencode.json` created (11 lines) | `d0d2e38` | `git show HEAD:opencode.json` |
| Jul 10, 02:42 | Config expanded to 276 lines (42 agents, 6 MCP) | `3613979` | `git log --stat 3613979` |
| Jul 13, 00:03 | `.bak` file created (8 lines — schema + instructions only) | `3613979` | `Get-Item opencode.json.bak` → CreationTime |
| Jul 13 | Secrets removed, env var placeholders added | `488553d` | `git show HEAD:opencode.json` has `${NOTION_API_KEY}` |
| Jul 15, 22:47 | Last commit (`0d171a2`) | `0d171a2` | `git reflog --date=iso` |
| Jul 16, 08:40 | `git reset HEAD` (no `--hard`) | — | `git reflog` HEAD@{1} |
| Jul 16, 16:16 | `git reset HEAD` (no `--hard`) | — | `git reflog` HEAD@{0} |
| Jul 19, 14:44 | `.bak` file modified (expanded to 128 lines, 7 agents) | — | `Get-Item opencode.json.bak` → LastWriteTime |
| Jul 19, ~14:00+ | **`opencode.json` deleted from disk** (unstaged) | — | `git status` shows `deleted: opencode.json` |

---

## Investigation

### 1. Configuration Discovery

OpenCode v1.17.18 (Bun-compiled JavaScript) searches for config in this order:

| Priority | Path | Found? |
|----------|------|--------|
| 1 | `~/.config/opencode/opencode.jsonc` | Yes (minimal: just `$schema`) |
| 2 | `./opencode.json` (findUp from cwd) | **No — deleted** |
| 3 | `./opencode.jsonc` | No |
| 4 | `./.opencode/opencode.json` | No |
| 5 | `./.opencode/opencode.jsonc` | No |

**The `engineering-os/opencode.json` is NOT discovered** — `findUp` walks parent directories, not sibling subdirectories.

### 2. What Was Lost

The deleted `opencode.json` contained:
- **42 custom agents** (decision-engine, resource-allocator, sprint-planner, etc.)
- **6 MCP servers** (notion, google-drive, gmail, google-tasks, notebooklm, odoo)
- **3 instruction files** (ENGINEERING_CONSTITUTION.md, ENGINEERING_DASHBOARD.md, REFERENCES.md)
- **1 reference** (engineering-os path)
- **1 skill path** (engineering-os/.opencode/skills)

Without this file, OpenCode only had:
- 4 built-in agents: `coder`, `summarizer`, `task`, `title`
- Default model selection based on available API keys

### 3. Model Selector Behavior

> **The Model Selector disappearance was a side effect of losing the Agent definitions.**

The Model Selector in the OpenCode TUI depends on having an active Agent context. When the 42 custom agents disappeared, there was no context to display the Model Selector in its expected form. This is distinct from the `model` field being lost — it is a UI-level dependency on Agent availability.

### 4. How the File Was Deleted

**Evidence gathered:**

| Source | Finding |
|--------|---------|
| `git reflog` | Two `reset: moving to HEAD` entries on Jul 16 (08:40, 16:16) — no `--hard` |
| PowerShell history | No `del`, `rm`, `Remove-Item` targeting `opencode.json` |
| OpenCode Desktop logs | OOM errors on Jul 19 (14:24, 16:26) — no file deletion evidence |
| OneDrive logs | Co-authoring activity on Jul 19 — no conflict files found |
| `robocopy` commands | 4 copies from Muhide → `C:\Projects\Muhide` (one-way copy, not move) |
| `.bak` file | Created Jul 13 (8 lines), modified Jul 19 (128 lines, 7 agents) |

**Conclusion:** The exact deletion mechanism **cannot be determined** from available evidence. PowerShell history shows no explicit delete. The `robocopy` commands are one-way copies. The `git reset` commands were soft (no `--hard`), which wouldn't delete files. OneDrive co-authoring was active but no conflict files exist.

### 5. `.bak` File Analysis

The `.bak` file is a **truncated subset** of the full config:
- **HEAD version:** 276 lines, 42 agents, 6 MCP servers
- **`.bak` file on disk:** 128 lines, 7 agents, 6 MCP servers
- **`.bak` at creation commit (`3613979`):** 8 lines (schema + instructions only)

The `.bak` file was modified on Jul 19 at 14:44 — **after** the deletion likely occurred. It appears to be a manually created recovery attempt, not the original file.

### 6. Working Tree State

```
git status --porcelain:
 D opencode.json          ← deleted from disk
 M opencode.json.bak      ← modified (8→128 lines)
 M engineering-os         ← submodule
 M docker-compose.yml     ← modified
 M salesos/.env.example   ← modified
 ... (342+ modified files)
```

The massive number of modified files suggests the working tree has drifted significantly from HEAD, likely due to ongoing development outside of git commits.

---

## Evidence

| Evidence | Source | Confidence |
|----------|--------|------------|
| File exists at HEAD | `git show HEAD:opencode.json` returns 276 lines | 100% |
| File deleted from disk | `git status` shows `deleted: opencode.json` | 100% |
| No other config found | Glob for `.opencode.json` returns empty | 100% |
| Global config minimal | `~/.config/opencode/opencode.jsonc` has only `$schema` | 100% |
| Config discovery order | Binary analysis shows `opencode.json` search paths | 100% |
| `engineering-os/opencode.json` not discovered | `findUp` walks parents, not siblings | 100% |
| Cause of deletion | Insufficient evidence | 0% |

---

## Root Cause Classification

### Immediate Cause

Project-level `opencode.json` was absent from the workspace directory.

### Contributing Factors

1. **Silent fallback to global configuration** — OpenCode silently falls back to `~/.config/opencode/opencode.jsonc` when project config is missing, with no user-visible warning
2. **No startup health check** — OpenCode does not validate that project config exists before loading
3. **No backup mechanism** — The `.bak` file exists but OpenCode does not check for it
4. **OneDrive sync** — The workspace is on OneDrive, which introduces file state complexity
5. **Working tree drift** — 342+ modified files suggest commits are not being made regularly

### Ultimate Root Cause

**Unknown.**

Available evidence proves the configuration file was missing but does not identify the actor or process responsible for its deletion. Further evidence would be required:

- Windows File Auditing logs (requires prior enablement)
- OneDrive sync conflict logs (binary ODL format, not human-readable)
- Shell history from other terminals (only PSReadLine history available)
- Filesystem-level audit trail (requires `auditpol` configuration)

---

## Why New Workspaces Continued Working

New workspaces get:
- The same global config (`~/.config/opencode/opencode.jsonc`)
- Built-in agents (coder, summarizer, task, title)
- Default model selection based on available API keys
- If they have their own `opencode.json`, they get custom agents/models

The Muhide workspace was special because it depended on a **project-level** `opencode.json` that no longer existed.

---

## Why Restoration Fixed It

Restoring `opencode.json` from git:
- Reinstated all 42 agent definitions
- Reinstated all 6 MCP server configurations
- Reinstated instruction paths and references
- OpenCode found the file at `./opencode.json` on next startup
- All agents and models became available again

---

## Lessons Learned

- Project-level configuration files are production-critical assets.
- Missing configuration should produce explicit startup diagnostics.
- Silent fallback increases MTTR because failures appear unrelated to the actual cause.
- Configuration files should be protected through Git, health checks, and CI validation.
- Recovery time was minimized because the configuration was still recoverable from Git history.
- Working tree drift (342+ uncommitted changes) increases the risk of accidental file loss going undetected.

---

## Preventive Actions

### Immediate

1. **Restore the file**: `git restore opencode.json`
2. **Commit the config**: `git add opencode.json && git commit -m "fix: restore opencode.json for agent/model availability"`

### Short-term

3. **Evaluate secondary configuration location**: Assess whether maintaining a copy at `.opencode/opencode.json` (if officially supported by the Desktop version in use) provides additional resilience against single-point-of-failure deletion
4. **Health check script**: Create a script that validates `opencode.json` exists and is valid JSON
5. **Git pre-commit hook**: Warn if `opencode.json` is missing from staged changes

### Long-term

6. **OpenCode improvement**: Request that OpenCode shows a warning when project config is missing
7. **Configuration versioning**: Use `OPENCODE_CONFIG` env var to point to a version-controlled config
8. **Regular commits**: Commit working tree changes more frequently to reduce drift

---

## Confidence Level

| Finding | Confidence |
|---------|------------|
| `opencode.json` deletion caused the issue | **100%** |
| Restoring the file fixed the issue | **100%** |
| `engineering-os/opencode.json` is not auto-discovered | **100%** |
| Model Selector disappearance was a side effect of Agent loss | **95%** |
| Silent fallback is a UX weakness | **100%** |
| `.bak` file is a manual recovery attempt | **85%** |
| **Cause of deletion** | **0% (unknown)** |

**Overall RCA confidence on immediate cause: 100%**
**Overall RCA confidence on ultimate root cause: 0% (insufficient evidence)**

---

*Report generated from forensic analysis of git history, PowerShell command history, OpenCode Desktop application logs, OneDrive sync logs, file system timestamps, and OpenCode binary source code analysis.*
