# Static-Type Sweep + Phase 6 Evidence Type-Contract Fix — 2026-09-23

## What this is

After finding two real, live bugs by hand this session (reports 62/63), this
report tries a more systematic method: running `mypy` (this repo's own
configured strict config, `pyproject.toml [tool.mypy]`) across `app/`, `sdk/`,
`domains/` and filtering to the specific error classes that would have
caught the cache-router bug (`attr-defined`, `call-arg`, `arg-type` — "calls
a method/argument that doesn't actually match the target's real type").

## Method and honest result

`mypy app sdk domains --show-error-codes` filtered to
`[attr-defined]|[call-arg]|[arg-type]` produced **52 findings**. The
`[no-untyped-def]` noise (hundreds of missing-return-type-annotation
warnings, expected in a codebase not written mypy-strict-clean) was
excluded entirely — it is not the class of bug this sweep was looking for.

Of the 52, the large majority are the same recurring, low-value pattern:
a SQLAlchemy `Column`/`Mapped` field typed `Optional` in the ORM model but
passed into a plain-dataclass or a second constructor that mypy sees as
requiring the non-Optional type. At runtime these are essentially always
populated (DB defaults, or the code path guarantees non-null before this
point), so mypy is flagging a real type-precision gap without there being
an actual behavior bug — fixing all 52 properly (tightening ORM Optionality
or adding narrowing) is a legitimate, larger type-hygiene project, not
something to rush through as a side effect of this sweep. **This report
does not fix those 51.** It fixes the one finding that inspection confirmed
is a real bug with real consequences, and documents the rest honestly as
unconverted static-analysis leads for a dedicated future pass.

## The one real bug found and fixed

`app/modules/master_data/phase6/pipeline.py:652` (inside
`Phase6Pipeline._stage_contact_relationships`), flagged by mypy as:

```
error: Argument "email_domain_match" to "infer_relationship" has
incompatible type "Literal[''] | bool | None"; expected "bool"  [arg-type]
```

The code built the argument with a bare `and`-chain:

```python
email_domain_match=(
    person_domain.get(person_id) and company_domain.get(company_id)
    and person_domain[person_id] == company_domain[company_id]
),
```

Python's `and` returns the *last evaluated operand*, not a coerced `bool`.
When either domain lookup misses (`.get()` returns `None`) or returns an
empty string, the whole expression evaluates to that `None`/`''` — not to
`False` — even though `infer_relationship()`'s signature declares
`email_domain_match: bool = False` and this codebase's own Phase 6/Phase 7
work has repeatedly emphasized exact evidence-field correctness (VERIFIED
vs INFERRED bases, field-level agreement, no implicit typing — see AGENTS.md
§34–37 and reports 41–47).

**Consequence, checked before fixing, not assumed:** `relationships.py`'s
own `elif email_domain_match:` branch check is unaffected — `None` and `''`
are falsy exactly like `False`, so the INFERRED/UNKNOWN classification
outcome does not change for this specific branch. The real defect is one
line later: `"email_domain_match": email_domain_match` stores the **raw,
possibly non-bool value** into the returned relationship-evidence dict.
Any downstream consumer that persists this to JSONB and later queries or
compares it strictly (`is False`, `= 'false'` in a JSON query, a
schema/type validator) would see `null` or `""` where the contract promises
`true`/`false` — a real, if narrow, evidence-integrity gap in exactly the
kind of field this project's Phase 6/7 work treats as load-bearing.

**Fix:** wrapped the same expression in `bool(...)`. Zero change to the
`elif` truthiness outcome (verified by reading `relationships.py`); the
only change is that the stored evidence field is now always a real `bool`,
matching its declared type.

## Verification

- `python -m py_compile` and `ruff check --select=E4,E7,E9,F,I` on the
  changed file: **PASS**.
- `tests/unit/test_phase6_relationships.py` (the existing suite for
  `infer_relationship` itself, unmodified): **6/6 PASS** — confirms the
  downstream function's behavior is unaffected by this caller-side fix.
- The DB-backed integration suite for this pipeline
  (`tests/integration/test_phase6_pipeline.py`, 20 tests) was **not**
  re-run this session — it needs a Phase 6 schema and seeded
  contact/company rows, a larger environment lift than this one-line,
  behavior-preserving-for-the-only-consumer-checked fix justified. The
  correctness argument above is verified by direct code inspection of both
  the call site and the sole consumer, not assumed.

## Deliberate non-claims

- This is not a full mypy remediation. 51 of 52 filtered findings remain
  open, cataloged below for whoever picks up a dedicated type-hygiene pass.
- Does not claim the Optional/required `arg-type` findings elsewhere are
  bugs — most inspected are ORM-Optional-into-dataclass patterns that are
  very likely benign at runtime; none of the other 51 were individually
  verified as real bugs or false positives this session.
- No database, migration, deployment, commit, or push occurred.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. This is
  a narrow correctness fix to an evidence field, not a Phase 7 or
  production-readiness change, and does not touch any canonical/promoted
  data — Phase 6 pipeline output remains `salesos_test`-only per existing
  gates.

## Full filtered mypy output (for whoever does the dedicated pass)

```
app/modules/master_data/phase6/pipeline.py:653  [arg-type]   FIXED (this report)
app/modules/company/signal_persistence.py:183,209,231  [attr-defined]  "Result[Any]" has no attribute "rowcount" — likely SQLAlchemy stub precision (CursorResult vs Result), not inspected further
app/modules/master_data/muhide_adapter.py:457  [attr-defined]  "object" has no attribute "append" — dict-literal value-type widening (mixed int/list values in one dict), likely a TypedDict-modeling gap, not inspected further
domains/ubom/__init__.py:64,67,107,133  [arg-type]/[attr-defined]  UBOM is already marked DEPRECATED per Phase 1 (AGENTS.md §12) — lower priority
domains/copilot/telemetry_service.py:101  [arg-type]  list[int] into a percentile helper expecting list[float]
domains/commercial/pipeline/engine/forecast_engine.py:56  [arg-type]  float into an int field
domains/search/engine/postgres_repo.py:347,407  [arg-type]  Optional float/str into a cursor-predicate helper
domains/employee/signals.py:153  [arg-type]  Any|list[Any] into a dict[str, Any] parameter
domains/decision_center/service.py:305  [arg-type]  Collection[str] into str/dict params (likely an unpacking-order bug — worth a closer look in a dedicated pass)
domains/revenue/analytics/postgres_repo.py:110-111, domains/feature_store/postgres_repo.py (×6), domains/workflow/postgres_repo.py (×11), domains/timeline/engine/postgres_repo.py (×5), domains/decision_center/postgres_repo.py:124,137,140  [arg-type]  the recurring ORM-Optional-into-required-dataclass-field pattern described above
domains/workflow/engine.py:200  [arg-type]  Optional str into a condition evaluator
domains/workflow/engine.py:395  [arg-type]  "dict[str, Any] | BaseException" appended where dict is expected — likely from an `asyncio.gather(..., return_exceptions=True)` result list; worth a closer look in a dedicated pass, not inspected this session
domains/workflow/postgres_repo.py:420  [attr-defined]  a step list typed as possibly-None treated as always-iterable
```
