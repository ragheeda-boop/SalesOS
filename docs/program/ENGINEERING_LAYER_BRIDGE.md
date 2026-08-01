# Engineering Spec Layer Bridge (ADR-036)

> **Purpose:** Program → `.engineering/` references only. **No data duplication.**  
> **Authority:** ADR-036 Phase 2 · Phase 0 criterion **9.2** · DEC-141  
> **Rule:** Business Truth lives here (`docs/program/`). Engineering Spec lives in `.engineering/`. Link; do not copy tables, counts, or sprint state across layers.

---

## Layer map (pointer only)

| Layer | Location | Owns | Does not own |
|-------|----------|------|--------------|
| Business Truth | `docs/program/` | Vision, roadmap, sprint, DEC-*, risks, Phase 0 exit | Architecture catalogs, ownership maps, EOS locks |
| Engineering Spec | `.engineering/` | Architecture, ADR index (EOS), capability map, locks, quality gates | Sprint board status, business priority |
| AI Runtime | `.ai/` | Deferred (ADR-036 §9.3) | — |
| Implementation | `salesos/` | Code, tests, infra | Governance prose |

Full four-layer decision: [`docs/adr/0036-engineering-organization-layer-separation.md`](../adr/0036-engineering-organization-layer-separation.md).

---

## Canonical Engineering Spec entry points

| Need | Path (do not duplicate contents here) |
|------|----------------------------------------|
| Constitution / freeze / truth hierarchy | [`.engineering/00_PROJECT_CONSTITUTION.md`](../../.engineering/00_PROJECT_CONSTITUTION.md) |
| Live runtime / blockers / locks mirror | [`.engineering/21_RUNTIME_STATE.json`](../../.engineering/21_RUNTIME_STATE.json) |
| File locks | [`.engineering/22_FILE_LOCKS.json`](../../.engineering/22_FILE_LOCKS.json) |
| Change protocol | [`.engineering/25_CHANGE_PROTOCOL.md`](../../.engineering/25_CHANGE_PROTOCOL.md) |
| Agent coordination | [`.engineering/26_AGENT_COORDINATION.md`](../../.engineering/26_AGENT_COORDINATION.md) |
| EOS ADR index | [`.engineering/27_ADR_INDEX.md`](../../.engineering/27_ADR_INDEX.md) |
| Capability registry (EOS view) | [`.engineering/29_CAPABILITY_REGISTRY.md`](../../.engineering/29_CAPABILITY_REGISTRY.md) |
| ARB EOS audit | [`.engineering/32_EOS_VALIDATION_AUDIT.md`](../../.engineering/32_EOS_VALIDATION_AUDIT.md) |
| Reverse bridge (engineering → program) | [`.engineering/33_PROGRAM_LAYER_BRIDGE.md`](../../.engineering/33_PROGRAM_LAYER_BRIDGE.md) |

---

## Reciprocal

Engineering agents enter Business Truth via [`.engineering/33_PROGRAM_LAYER_BRIDGE.md`](../../.engineering/33_PROGRAM_LAYER_BRIDGE.md).

---

## Honesty

- Fingerprint / EvidenceLevel / staleness: criteria **4.2 / 4.4 / 4.7** → **CLOSED** (DEC-142a). ARB re-audit residuals: **4.1 / 4.8** (separate).
- **Production GO not claimed. CI GREEN not met.**
