# 158 — `KafkaConsumerBase._deserialize()`: `aggregate_id` was silently discarded on every CloudEvents round trip

**Read-only in scope of production/salesos_test.** Pure unit-level fix; no database container needed.

## 1. Scope — completing the `sdk/events/` sweep

Continuing directly from report 156 (`sdk/events/outbox.py`'s double-serialization bug), reviewed `sdk/events/kafka_consumer.py` (`KafkaConsumerBase`), the consumer-side counterpart to `KafkaProducer`/`OutboxRelay`.

## 2. The bug

`DomainEvent.to_dict()` (`sdk/events/base.py`) encodes the CloudEvents 1.0 envelope's `subject` field as `f"{aggregate_type}/{aggregate_id}"` (or `""` when `aggregate_id` is unset) — this is the only place `aggregate_id` appears anywhere in that envelope; it is not a top-level key.

`_deserialize()`'s CloudEvents branch (`"specversion" in payload and "data" in payload`) never read `payload["subject"]` at all — it unconditionally hardcoded `aggregate_id=""` on every reconstructed `DomainEvent`, regardless of what the original event's `aggregate_id` actually was. `aggregate_type` *was* correctly recovered (from `payload["source"]`, stripping the `"salesos."` prefix), confirming the round trip was intentionally designed to preserve both fields — `aggregate_id` was simply never wired up on the read side.

## 3. Reachability

`grep -rln "KafkaConsumerBase" app/ domains/ runtime/ intelligence/ mcp_server/` (excluding the module itself and its own test file): **zero matches** — no subclass exists anywhere in the live application; `handle_event()` is never implemented outside the test file's own `CollectingConsumer`/`FailingConsumer`. Confirmed dead code, matching this session's now-familiar "correctly-designed-but-unwired component with a genuine internal defect" pattern (reports 121/123/126/127/130/131/135/156) — fixed ahead of any future wiring decision, since the defect is unconditional silent data loss, not a crash that would announce itself.

## 4. Why existing tests never caught it

`tests/unit/test_kafka_consumer.py::test_deserialize_cloud_events` never asserted on `event.aggregate_id` for the CloudEvents branch at all (only `event_id`/`event_type`/`tenant_id`/`data`). Its own fixture (`cloud_event_payload`) doesn't even include a `"subject"` key, so the bug was invisible to it either way. The legacy-format branch (`payload.get("aggregate_id", "")`, read directly as a top-level key) is correct and unaffected — `tests/unit/test_kafka_consumer.py::test_deserialize_legacy` exercises that path and was never at risk.

## 5. Fix

```python
subject = payload.get("subject", "")
aggregate_id = subject.split("/", 1)[1] if "/" in subject else ""
```
`split("/", 1)` splits on only the first `/`, so an `aggregate_id` value that itself happens to contain a `/` is preserved intact as the remainder rather than mis-split; an empty `subject` (no aggregate_id was ever set) correctly yields `""`, matching the original.

## 6. Verification — genuine red→green

Two new tests in `tests/unit/test_kafka_consumer.py`, both driving the **real** `DomainEvent.to_dict()` (not a hand-built fixture) through `_deserialize()` — a true producer/consumer round trip:
- `test_deserialize_cloud_events_recovers_aggregate_id_from_subject`: a `DomainEvent` with `aggregate_id="c-9001"` must come back with `aggregate_id == "c-9001"`.
- `test_deserialize_cloud_events_no_aggregate_id_when_subject_empty`: a `DomainEvent` with no `aggregate_id` set must come back with `aggregate_id == ""` (not fabricated).

Scoped `git stash push -- salesos/backend/sdk/events/kafka_consumer.py` (reverting only the fix): the first new test failed with the exact predicted `AssertionError: assert '' == 'c-9001'`. `git stash pop` restored the fix; both tests re-confirmed PASS.

Separately checked a "coroutine never awaited" warning surfaced by the pre-existing `test_subscribe_updates_topics` test: confirmed against the installed aiokafka source (`consumer/consumer.py:1017`) that `AIOKafkaConsumer.subscribe()` is a plain synchronous `def`, not `async def` — the production code's un-awaited `self._consumer.subscribe(topics=topics)` call is correct. The warning is a pre-existing test-fixture imprecision (that one test uses a blanket `AsyncMock()` for the whole consumer, making every attribute — including the genuinely-synchronous `subscribe` — resolve to an awaitable mock); not a production bug, not touched.

## 7. Regression

`test_kafka_consumer.py` (16, incl. the 2 new) + `test_outbox.py` (20) + `test_outbox_relay_value_serialization.py` (1, report 156): **37/37 PASS**. Ruff (`--select E4,E7,E9,F,I`) on both changed files: 0 findings. `python -m py_compile` and `git diff --check`: clean.

## 8. Scope and safety

- Two files touched: `salesos/backend/sdk/events/kafka_consumer.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_kafka_consumer.py` (2 new tests).
- No database or container needed. No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.
- A separate, concurrently-running session continues committing unrelated fixes directly to this branch (confirmed via `git log`: a new `0e8f1c14 fix(db): ...` commit landed mid-tick, touching only conftest/RLS-test files, disjoint from this work) — staged and committed only the two files listed above, by explicit path.

## 9. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the originally-planned `sdk/events/` sweep from report 155's broadened search (`outbox.py` → report 156, `kafka_consumer.py` → this report). One item remains from that list: `sdk/events/store.py` — noted in report 157 as one of DEC-156's six listed residual `MetaData()` islands (a schema-registration governance question, already GUC-pinning-fixed under DEC-157/report 114) — worth a full re-read to confirm no additional field-mapping or serialization bug exists there independent of that governance question, before moving to a fresh methodology or file family.
