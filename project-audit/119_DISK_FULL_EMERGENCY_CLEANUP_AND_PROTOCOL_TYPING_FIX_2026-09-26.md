# 119 — D: drive disk-full emergency (0 bytes free) resolved with owner approval; LLMProvider.chat_stream Protocol typing fix

## 1. Disk-full emergency

Mid-sweep, a routine `Edit` call failed with `ENOSPC: no space left on device`. `D:\AISalesOS` (a 15GB FAT32 volume, per report 107) had reached **0 bytes free, 100% used** — no further file could be saved, including AGENTS.md/report writes or any new git commit.

**Investigation, before touching anything:**
- `docker system df` showed large reclaimable Docker space, but `docker info` confirmed `Docker Root Dir: /var/lib/docker` — inside the WSL2 VM's own virtual disk, not on `D:`. Ruled out as irrelevant to this emergency.
- A PowerShell recursive size breakdown of `D:\AISalesOS` found the two largest consumers: `packages/` (5.6GB, of which `packages/packages` — an accidental self-nested duplicate — was 1.6GB) and `docs/` (2.1GB, of which `docs/docs` was 471MB). Six smaller nested duplicates were confirmed the same way: `.ai/.ai`, `.github/.github`, `assets/assets`, `.engineering/.engineering`, `infrastructure/infrastructure`, `migration-log/migration-log`.
- **All eight had already been identified by report 107/151 as "apparent copy accident" and explicitly deferred to the owner** — never authorized for deletion by any prior session.
- `packages/data` (3.95GB — Notion/identity import pipeline data, `notion_export`/`normalized`/`import`/`identity`/`golden`/`cleaned`) was inspected and left untouched: this is real business data, not a duplicate.
- `salesos_test_export/` held two old full-database dumps: `salesos_test_pre_repair_20260920.dump` (255MB, report 47's pre-repair safety net) and `salesos_test.dump` (249MB, from 2026-09-10) — both predating the current pinned-Global-ID restore (report 139) and therefore superseded, but still a form of backup/safety-net data, not source code.

**Before deleting anything**, each of the 8 flagged nested duplicates was verified structurally: the *outer* directory (e.g. `.github/`) was confirmed to hold its own complete, independent copy of the expected content (`workflows/`, `CODEOWNERS`, `dependabot.yml`), separate from the *inner* nested duplicate — ruling out any chance that the nested copy was actually the only copy of something real.

**Asked the owner directly** (this was a hard-to-reverse, destructive action outside the scope of the standing Phase-7 loop authorization, and explicitly deferred by two prior sessions for exactly this reason). The owner approved both: delete the 8 nested-duplicate directories and delete the 2 superseded database dumps.

**Executed, in order:**
1. Deleted all 8 nested-duplicate directories via `Remove-Item -Recurse -Force`, confirmed each no longer exists afterward.
2. Deleted the 2 superseded `.dump` files, confirmed each no longer exists afterward.
3. Re-checked disk space: **2.76GB free** (was 0).

**Git impact: none.** `git status --porcelain --ignore-submodules=all` on all 9 deleted paths shows no entries at all (not even as deletions) — every one of them was already untracked (`??` before deletion, nothing after). No commit was needed to reconcile this; it is pure filesystem hygiene, not a repository change.

## 2. LLMProvider.chat_stream: Protocol stub misdeclared as async

Found via a repo-wide filtered mypy sweep (continuing report 64's methodology: `mypy app/ sdk/ domains/`, which also visits transitively-imported files under `intelligence/`, `runtime/`, `benchmarks/`, `demo/`) — 243 filtered (`[attr-defined]`/`[call-arg]`/`[arg-type]`) findings this run, up from report 64's 52 (a different, narrower scope; not a regression).

`intelligence/providers/protocol.py`'s `LLMProvider` Protocol declared:
```python
async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
    ...
```
With no `yield` in the stub body, mypy correctly infers this signature as returning `Coroutine[Any, Any, AsyncIterator[StreamEvent]]` — a coroutine that, once awaited, *produces* an async iterator — not a value that is itself directly async-iterable. This surfaced as 3 errors at the call site in `intelligence/providers/reliability.py`:
- Line 304: `"Coroutine[...]" has no attribute "__aiter__" (not async iterable)`.
- Lines 314, 341: `Argument "embedding" to "EmbeddingResponse" has incompatible type "list[list[Never]]"` (a *separate* finding on nearby lines, addressed below — not caused by the same root issue).

**Reachability and runtime correctness, checked before fixing:** every concrete provider (`anthropic_provider.py`, `azure_provider.py`, `gemini_provider.py`, `ollama_provider.py`, `openai_provider.py`) declares `chat_stream` as a real `async def` generator with `yield` inside — genuinely async-iterable at runtime, regardless of the Protocol's stated type. A repo-wide grep for every call site of `.chat_stream(` found exactly two (`intelligence/agents/llm.py:358`, `intelligence/providers/reliability.py:304`), and both already use the correct `async for event in provider.chat_stream(request):` pattern. **This was not a live bug** — nothing is broken today. The risk was purely latent: with the Protocol's return type wrong, a *future* regression that accidentally introduced an `await`-then-iterate bug at either call site would not be caught by mypy, since it already "expected" a bare Coroutine there.

**Fix:** declared the Protocol method as `def` (no `async`) — the correct way to model an async-generator-returning callable in a `Protocol`/interface under PEP 544; concrete implementations are unaffected since Python doesn't require an implementation's `async`/non-`async` keyword to textually match a Protocol's. Confirmed `LLMProvider` is not `@runtime_checkable` and no `isinstance()` check anywhere depends on this, so this is purely a static-typing correction with zero runtime effect.

**Verification:** `mypy intelligence/providers/reliability.py` no longer reports the `chat_stream`/`__aiter__` finding (confirmed via targeted grep on fresh output). Full `tests/unit/test_ai_foundation_f1.py` + `f2` + `f3` suite: **95/95 PASS**. Ruff (`E4,E7,E9,F,I`) and `compileall` clean.

## 3. The two adjacent `EmbeddingResponse` findings (lines 314, 341) — checked and NOT a bug, but a correction to how this was first described

`ReliableProvider.embed()`'s two failure-path fallbacks return:
```python
embedding=[] if isinstance(request.text, str) else [[]]
```
against `EmbeddingResponse.embedding: list[float] | list[list[float]]` (`intelligence/providers/base.py:62`, a plain dataclass field — **not** the dict/tuple-literal value-type-widening shape this session already confirmed as a recurring false positive in reports 64/66/110/112, and this report's commit message initially, incorrectly, said it was). mypy infers the literal `[[]]`'s inner empty list as `list[Never]`, which it does not accept as satisfying the `list[list[float]]` union member here — a distinct, narrower nuance about empty-list-literal inference inside a nested generic Union, not the same mechanism as the dict-literal cases.

Checked the *actual* consumer to determine whether this shape mismatch has a real runtime consequence: `intelligence/agents/llm.py:431-433` is the only caller that inspects `response.embedding`, and it explicitly handles both shapes — a flat `list[float]` is returned directly, otherwise `response.embedding[0]` (the first inner list) is returned. For the batch-failure fallback `[[]]`, this correctly yields `[]` (an empty embedding), exactly the intended "no embedding produced" signal. **Not a functional bug** — the sole real caller already tolerates this exact fallback shape correctly. Left unfixed, matching this session's established practice of not chasing confirmed-benign mypy noise.

**Correction to this report's own commit message:** commit `a25fd1d7`'s message states these two lines were "confirmed separately as pre-existing, unrelated dict/list value-type-widening false positives" — that description is inaccurate. They are a *different* mypy inference nuance (empty-list-literal-in-nested-Union), independently checked and confirmed benign via caller analysis, not the same mechanism as the `phase6/pipeline.py`/`muhide_adapter.py` findings actually checked for that shape. The conclusion (false positive, no fix needed) still holds; the stated reasoning in the commit message does not. Recorded here rather than rewriting the already-created local commit, per this session's standing instruction to create new commits, not amend.

## 4. Two more findings checked and confirmed as the already-established false-positive shape

- `app/modules/master_data/phase6/pipeline.py:552` (`"object" has no attribute "clear"`) — `_reset_run_state()` iterates a tuple of several `list[dict[str, Any]]` / `list[tuple[Any, ...]]` attributes; mypy widens the loop variable's type to `object` across the heterogeneous element types. All are genuine lists (`= []` declared at `__init__`, `.clear()` exists on every real list). Confirmed false positive, matching reports 64/110's pattern.
- `app/modules/master_data/muhide_adapter.py:457` (`"object" has no attribute "append"`) — `report["discrepancies"]` is a genuine `list` (`= []` in the dict literal alongside integer counters); mypy widens the dict-literal's value type across the mix. Same shape as report 64/110's original finding in this exact file. Confirmed false positive.
- `benchmarks/runner.py:141-148` (`"Sequence[str]" has no attribute "append"`) — same recurring dict-literal value-type-widening shape (`comparison` mixes `str` values with `list` values); `benchmarks/` is a dev-only tool, not reachable in any live request path. Confirmed false positive, not pursued further given the established diminishing-returns pattern from report 66/112.

## 5. Scope and safety

- **Files changed (git):** `salesos/backend/intelligence/providers/protocol.py` (1 line). Commit `a25fd1d7`.
- **Filesystem changed (not git-tracked, owner-approved):** 8 nested-duplicate directories and 2 superseded database dumps deleted from `D:\AISalesOS`, freeing ~2.76GB.
- No production/`salesos_test` write; no provider call; no Phase 7 gate touched.
- Loop status: continuing the standing "5 hours, all approvals" authorization, scoped to code-level fixes with red→green proof — the disk-space decision was explicitly carved out and put to the owner first, since it was destructive and outside that authorization's scope.
