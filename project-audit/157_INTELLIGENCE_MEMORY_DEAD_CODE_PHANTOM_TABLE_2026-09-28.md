# 157 — `intelligence/memory/` is entirely dead code with a phantom (never-created) `episodic_memory` table; documented, not fixed

**Read-only.** No files changed, no database container needed — this is a reachability/architecture finding, not a bug fix.

## 1. Scope

Continuing the broadened `_row_to_*`/`_from_row`/etc. sweep, reviewed `intelligence/memory/postgres_store.py` (`PostgresMemoryStore`) alongside the rest of the `intelligence/memory/` package it belongs to (`base.py`, `working.py`, `session.py`, `conversation.py`, `retrieval.py`, `store.py`).

## 2. What's in the file

`PostgresMemoryStore.store()`/`get()`/`query()`/`delete()`/`clear()`/`cleanup_expired()` are all internally consistent — `_row_to_entry()`'s construction matches every column the various `select()`s project, and the module's own comment discloses its design honestly:

```python
# Lightweight table()/column() — avoid private MetaData island (EAB-001-P1-DRIFT-01).
# DML stub only; not copied onto Base (DEC-156 would be required for that merge).
episodic_memory = table("episodic_memory", column("id", String(64)), ...)
```

This is not accidental drift — it is a deliberate, self-documented `table()`/`column()` DML stub, matching the same governance pattern `DEC-156-METADATA-BASE-MERGE-RESIDUAL.md` (Proposal, not Accepted) exists to eventually resolve for other files. However, checking DEC-156's own residual-islands table shows `intelligence/memory/postgres_store.py` is **not** one of its six listed items (`app/db05_orphan_keep.py`, `runtime/activity_runtime/__init__.py`, `sdk/events/store.py`, `runtime/knowledge_graph_runtime/repository/sql_repository.py`, `domains/search/engine/vector_store.py`, `sdk/events/outbox.py`) — the DEC's own text says those six are what remained *after* a 2026-08-13 land already converted "seven query/DML stubs" to `table()`/`column()` without a Base merge, and that conversion "does not require this DEC." `intelligence/memory/postgres_store.py`'s stub appears to be one of those seven already-accepted-as-a-stub files — its `table()`/`column()` form itself is not the open governance question.

The deeper problem is different and more basic: **no code path anywhere creates the `episodic_memory` table at all.**

- `grep -rln "episodic_memory" app/alembic/versions/*.py` → **zero matches**. No migration, past or head, ever creates this table.
- Unlike `sdk/events/outbox.py`'s `EventOutbox` (DEC-156 item 6), which at least has an `ensure_table()` method calling `_outbox_metadata.create_all(sync_connection, checkfirst=True)` as a runtime-DDL bootstrap fallback, `PostgresMemoryStore` has **no such method at all** — it assumes the table already exists and goes straight to `INSERT`/`SELECT`/`DELETE`.

So even setting the DEC-156 stub-governance question aside entirely, `PostgresMemoryStore` would fail with `UndefinedTableError` on its very first call in any environment, by any caller, forever — there is no path by which this table could ever come to exist.

## 3. Reachability — confirmed fully dead, re-verified this tick

Re-ran all three supporting greps fresh (not relying on the prior tick's now-stale results):

```
grep -rln "episodic_memory" app/alembic/versions/*.py         → (none)
grep -rln "PostgresMemoryStore(" app/ domains/ runtime/ intelligence/ sdk/ mcp_server/ \
    | grep -v intelligence/memory/postgres_store.py            → (none)
grep -rln "from intelligence\.memory\|import intelligence\.memory" app/ domains/ runtime/ mcp_server/  → (none)
```

Widened further this tick: `intelligence/memory/__init__.py` exports six public names (`WorkingMemory`, `SessionMemory`, `ConversationMemory`, `MemoryRetrieval`, `InMemoryMemoryStore`, `PostgresMemoryStore`). A grep for those names outside `intelligence/memory/` surfaced apparent hits in `app/modules/tenant_studio/ai_memory.py`/`ai_memory_router.py`/`ai_memory_store.py`/`postgres_ai_memory_store.py` — checked each directly: every one of these defines and uses **its own, entirely separate** `ConversationMemory` class (e.g. `app/modules/tenant_studio/ai_memory.py:44: class ConversationMemory:`), with **zero** `from intelligence` or `import intelligence` statements anywhere in any of the four files. This is coincidental name reuse between two independently-built features, not a shared import. `app/modules/tenant_studio/postgres_ai_memory_store.py` is the genuinely live, previously-verified-correct AI Memory persistence layer (report 89: "AI Memory uses opt-in encrypted turns, TTL, caps, and opt-out deletion"), entirely unrelated to and not depending on `intelligence/memory/` in any way.

**Conclusion, now doubly confirmed**: the entire `intelligence/memory/` package — all six exported classes — has zero consumers anywhere in the live application. It appears to be an earlier, abandoned implementation of the same conceptual feature that was later rebuilt from scratch as `app/modules/tenant_studio/`'s AI Memory, without the old package ever being removed.

## 4. Why this is documented, not fixed

This does not match the "correct dead code ahead of future wiring" pattern this session has repeatedly applied (reports 121/123/126/127/130/131/135/135/156) — in every one of those cases, the dead code was a genuine, still-relevant component whose eventual wiring was plausible and whose defect was narrow and mechanical to fix (a field-name mismatch, a missing GUC pin, a double-serialization). Here, fixing `PostgresMemoryStore` to actually work would require:

1. Writing a new Alembic migration to create `episodic_memory` (a genuine schema decision — column types, indexes, retention/TTL enforcement strategy, and whether it should be a tenant-scoped RLS table at all, none of which this session can respons‌ibly infer), **or**
2. Deleting the entire package as superseded dead code.

Both are product/architecture decisions this session should not make unilaterally — the same discipline already applied to `workflow_service`'s gap (report 152), the `google_maps` provider gate (report 85/29), and the NULL-idempotency-key gaps (reports 87/147). Silently creating a migration for a feature that may have been deliberately abandoned in favor of the tenant_studio rebuild would be presumptuous; silently deleting a package without confirming it is truly obsolete (rather than paused/pending) would be equally presumptuous.

## 5. Scope and safety

- No files changed. No database or container needed for this investigation — pure reachability analysis.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.
- Flagging this as a candidate for a product/architecture decision (delete `intelligence/memory/` entirely, or build out its persistence and actually wire it in place of/alongside the tenant_studio implementation) — not acting on it further without that decision.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. Next: `sdk/events/kafka_consumer.py` (unchecked), and a fresh confirmation pass on `sdk/events/store.py` — noting it is explicitly one of DEC-156's six listed residual `MetaData()` islands (item 3: `domain_events` Index KEEP, copied in `app/database.py`), which is a schema-registration governance question distinct from the GUC-pinning fix report 114/DEC-157 already applied to that same file — worth re-reading in full to confirm no additional field-mapping or serialization bug exists there independent of the DEC-156 question.
