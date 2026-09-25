# EXTERNAL DEPENDENCY REGISTER — 2026-08-24

**Purpose:** Track all external dependencies blocking Phase E / Production GA.

---

## Register

| ID | Dependency | Owner | Status | Blocking | Notes |
|----|------------|-------|:------:|:--------:|-------|
| EXT-01 | Staging environment access | Infrastructure / Admin | BLOCKED | E | Railway service + DB + Redis + OAuth + Vercel frontend |
| EXT-02 | LLM provider selection | Management (PO + TL + Finance) | BLOCKED | E | 4 qualified providers; see ADR-LLM-PROVIDER-SELECTION.md |
| EXT-03 | Railway Owner/Admin permissions | Platform (Railway Owner/Admin) | BLOCKED | E | Enable managed backup schedule + PITR |
| EXT-04 | External pentest | Security / Management | BLOCKED | GA | Requires EXT-01 (staging) first; can run in parallel with Phase E |

---

## Resolution Criteria

| ID | Resolved When |
|----|---------------|
| EXT-01 | Staging backend URL returns 200 on `/health`; staging DB accepts `alembic upgrade head`; staging OAuth client returns valid JWT |
| EXT-02 | Provider selected; API key provisioned via GitHub Environments; `feature_ai_copilot=True` in staging |
| EXT-03 | Railway dashboard shows "Backups: Enabled" with daily schedule; restore drill completed |
| EXT-04 | Pentest report received; all P0/P1 findings remediated or accepted with risk sign-off |

---

## Dependency Graph

```
EXT-01 ──┬──> D.5 CLOSED ──> D.6 Gate Review ──> Phase E
EXT-02 ──┤
EXT-03 ──┘

EXT-01 ──> EXT-04 (pentest needs staging)
EXT-04 ──> GA Gate (pentest PASS required for GA)
```

---

## Escalation

| ID | Escalation Path |
|----|-----------------|
| EXT-01 | Ask Infrastructure team: "When can we get a staging Railway project + separate Postgres?" |
| EXT-02 | Ask Management: "Which LLM provider? OpenAI / Azure / Google / Anthropic?" |
| EXT-03 | Ask Platform: "Can you enable managed backups on the Railway project?" |
| EXT-04 | Ask Security: "When can we engage a pentest provider?" |

---

## Status Legend

- **BLOCKED** — Cannot proceed without external action
- **IN PROGRESS** — External action underway
- **RESOLVED** — Condition met; evidence recorded

---

**Current status: ALL BLOCKED — awaiting external actions.**
