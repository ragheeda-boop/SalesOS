# 156 — `OutboxRelay._deliver_one()`: every message's payload was double-serialized, corrupting it before it ever reached Kafka

**Read-only in scope of production/salesos_test.** Pure unit-level fix (mocked producer); no database container needed — the defect is in message serialization, not persistence.

## 1. Scope — resuming the "domain/DB-model conversion" sweep in `sdk/events/`

Per the standing loop's broadened search pattern (`_row_to_*`/`_from_row`/etc.), reviewed `sdk/events/outbox.py` (`EventOutbox`/`OutboxRelay`). `EventOutbox`'s own CRUD (`write`/`mark_delivered`/`mark_failed`/`mark_dlq`/`fetch_pending`/`fetch_dlq_count`/`cleanup_delivered`/`_row_to_entry`) is fully correct: `_row_to_entry()`'s 12-field construction matches `fetch_pending()`'s 12-column `select()` exactly, index for index; every raw SQL use is via SQLAlchemy Core constructs (`insert()`/`update()`/`delete()`/`select()`), never a `text()` bind-cast that could hit the `:name::type` scanner quirk found repeatedly elsewhere this session. No RLS/tenant concern applies: `event_outbox` deliberately has no `tenant_id` column — it is a platform-level relay queue read by a single background process across all tenants, not a tenant-scoped API table.

The bug is not in persistence at all — it is in `OutboxRelay._deliver_one()`, the method that actually hands a fetched entry's payload to the real Kafka client.

## 2. The bug

`kafka_producer.py` constructs the real `AIOKafkaProducer` with:
```python
value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
```
Confirmed directly against the installed `aiokafka` package's source (`producer/producer.py:350-357`): `Producer._serialize(topic, key, value)` applies `self._value_serializer(value)` **unconditionally** whenever one is configured — there is no way to bypass it per-call by pre-encoding the value yourself.

`_deliver_one()` did exactly that — pre-encoded the payload before calling `.send()`:
```python
await self._producer._producer.send(
    topic,
    value=json.dumps(payload, default=str).encode("utf-8"),
    ...
)
```
This bytes object is then handed to the configured `value_serializer`, which calls `json.dumps(some_bytes, default=str)`. `bytes` is not JSON-serializable, so the `default=str` fallback fires, serializing `str(some_bytes)` — the **Python repr of the bytes object** — as a quoted JSON string. Reproduced directly:

```
pre_encoded (what _deliver_one built):  b'{"a": 1, "b": "hello"}'
what actually reaches the wire:         b'"b\'{\\"a\\": 1, \\"b\\": \\"hello\\"}\'"'
json.loads() of that on the consumer side: 'b\'{"a": 1, "b": "hello"}\''  (a bare STRING, not the dict)
```

Every message relayed through the transactional outbox path would arrive at any real consumer corrupted beyond recovery — not merely malformed, but silently parseable into the wrong Python type (a string containing an unparsed repr), which could pass a naive `isinstance(x, str)`/truthiness check downstream and propagate garbage rather than failing loudly.

The `key=` parameter is unaffected: `kafka_producer.py` never configures a `key_serializer`, and `_serialize()`'s key branch falls through to using the raw value as-is when none is set (confirmed in the same aiokafka source read) — `entry.key.encode("utf-8")` was already correct.

## 3. Reachability — currently dead, but a guaranteed corruption the instant it's wired

Grepped `app/`, `domains/`, `runtime/`, `intelligence/`, `mcp_server/` for every `OutboxRelay(`/`set_outbox_relay(` reference: **zero** call sites outside `sdk/events/` itself. `KafkaEventBus` (the one class with an `_outbox_enabled` path) is genuinely instantiated at boot (`app/boot/startup.py:86`, `_init_event_runtime`, live), but that function never calls `set_outbox_relay()` — so `self._relay` stays permanently `None` on the live instance, and `publish()`'s outbox branch (`if self._outbox_enabled and self._relay is not None`) can never trigger regardless of the `kafka_outbox_enabled` setting. This matches the established "correctly-designed feature, never actually connected" pattern from reports 148/151 — except here the component itself carries a real, unconditional bug that would fire on its very first live message, not merely an absent wiring.

## 4. Why existing tests never caught it

`tests/unit/test_outbox.py::test_relay_publishes_pending_events` mocks `producer._producer = AsyncMock()` and asserts only `producer._producer.send.called` — an `AsyncMock` runs no real serializer, so a format bug in what's passed as `value=` is structurally invisible to it. No other existing test inspects the `value=` argument's content.

## 5. Fix

Removed the pre-encoding; pass the raw payload `dict` and let the producer's own configured serializer run exactly once — mirroring the correct, already-established pattern in the same codebase (`kafka_producer.py`'s own `KafkaProducer.publish()`: `value=event.to_dict()`, a raw dict, never pre-encoded).

```python
await self._producer._producer.send(
    topic,
    value=payload,
    headers=headers,
    key=entry.key.encode("utf-8") if entry.key else None,
)
```

## 6. Verification — genuine red→green

New `tests/unit/test_outbox_relay_value_serialization.py` calls `_deliver_one()` directly (not through the timing-dependent relay loop) against a fake `_producer.send()` that captures the raw `value=` argument, then applies the **same `value_serializer` lambda** `kafka_producer.py` configures `AIOKafkaProducer` with — reproducing exactly what aiokafka's own `_serialize()` would do to it, without needing a live broker or importing aiokafka's producer class.

- With the fix: `json.loads(REAL_VALUE_SERIALIZER(captured_value)) == sample_entry.payload` — PASS.
- Scoped `git stash push -- salesos/backend/sdk/events/outbox.py` (reverting only the fix), re-ran: failed with the exact predicted corruption —
  ```
  AssertionError: ... got 'b\'{"company_id": "c-777", "name": "Acme Corp", "amount": 12345}\'' (type str) instead
  ```
  — a bare string containing the escaped bytes-repr, not the dict. `git stash pop` restored the fix; re-confirmed PASS.

## 7. Regression

`tests/unit/test_outbox.py` (20 existing tests) + the new file: **21/21 PASS**. Ruff (`--select E4,E7,E9,F,I`) on both changed/added files: 0 findings. `python -m py_compile` and `git diff --check`: clean.

## 8. Scope and safety

- Two files touched: `salesos/backend/sdk/events/outbox.py` (one-line fix + explanatory comment), `salesos/backend/tests/unit/test_outbox_relay_value_serialization.py` (new).
- No database or container needed — this is a pure message-serialization defect, reproduced and fixed at the unit level against the real serializer function.
- No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.
- A separate, concurrently-running session is committing unrelated test/conftest fixes directly to this same branch (confirmed via `git status`/`git diff --stat` to touch entirely disjoint files) — staged and committed only the two files listed above, by explicit path.

## 9. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is the first real bug found via the broadened `sdk/events/` sweep begun after `icp_persistence.py`/`relationships/store.py` came back clean (report 155). Remaining candidates from that broadening: `sdk/events/kafka_consumer.py`, and a final confirmation pass on `sdk/events/store.py` (presumed already covered by DEC-157/report 114's GUC-pinning work — not yet re-verified this segment). The `intelligence/memory/postgres_store.py` investigation (dead code, phantom `episodic_memory` table, zero external consumers — superseded by the separate, live `app/modules/tenant_studio/postgres_ai_memory_store.py`) reached a firm conclusion in the prior tick but was not yet written up; carrying it forward as the next report.
