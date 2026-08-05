# AI Copilot Activation Guide

**Status:** Disabled by default — GA honesty  
**Authority:** [AI_HONESTY.md](../audit/ga-engineering-audit/AI_HONESTY.md) | [PRODUCTION_PLAN.md](../audit/ga-engineering-audit/PRODUCTION_PLAN.md)  
**Last updated:** 2026-08-06

---

## 1. What the AI Copilot does

The AI Copilot is an **experimental** assistant surface within SalesOS:

| Feature | Description |
|---------|-------------|
| Insights tab (`/copilot`) | AI-powered company research, deal analysis, and recommendations |
| Chat tab | Conversational query interface backed by agent coordinator |
| Branching | Multiple conversation threads with history and telemetry |
| Feedback loop | Users can rate responses; telemetry aggregates success rates and latency |
| Search tool | Agent can call `search_companies` to fetch structured data |

**Principle:** AI assists. Humans decide. Evidence governs.

---

## 2. Why it is disabled by default

Per **AI_HONESTY.md**, the audit classifies the AI surface as **not production-ready**:

- Backend `feature_ai_copilot` defaults to `False` in `salesos/backend/app/config.py`
- FE Decision package is a **stub** (throws on direct call)
- Product endpoints return **403** when the flag is off
- FE hides copilot UI (nav button, panel, `/copilot` route) when disabled
- Claiming "AI-native GA" is **forbidden** without evidence

---

## 3. Evidence gates (all required before activation)

Each gate must be independently verified. Check the box when complete:

- [ ] **Gate 1 — AI response quality measured (accuracy > 80%)**  
  Run `backend/tests/unit/test_story_14_07_llm_regression.py`.  
  Validation harness must pass with golden fixtures against live LLM.  
  Evidence: similarity scores > 0.80 across all domains.

- [ ] **Gate 2 — User feedback loop operational**  
  Verify `POST /api/v1/copilot/feedback` accepts and stores ratings.  
  Verify `GET /api/v1/copilot/telemetry` returns aggregated stats.  
  Confirm feedback data flows into telemetry dashboard.

- [ ] **Gate 3 — Decision Platform audit trail complete**  
  All copilot decisions must write to the Decision Platform with traceable IDs.  
  Verify `POST /api/v1/decision/evaluate` chain is exercised through copilot paths.  
  Audit log must include model, prompt, response, confidence, and tenant context.

- [ ] **Gate 4 — Prompt injection protections verified**  
  Run `backend/tests/unit/test_adversarial_entitlement_bypass_story_06_04.py`.  
  Copilot must not leak data across tenants or execute injected commands.  
  Rate-limiting and content filtering must be active.

---

## 4. How to enable

### Step 1: Set environment variable

In `salesos/frontend/.env.local` (or `.env`):

```bash
NEXT_PUBLIC_FEATURE_AI_COPILOT=true
```

### Step 2: Enable backend flag

In `salesos/.env`:

```bash
FEATURE_AI_COPILOT=true
```

### Step 3: Rebuild and restart

```bash
cd salesos
docker compose down
docker compose up -d --build
```

### Step 4: Verify

1. Check `GET /api/v1/copilot/status` returns `feature_ai_copilot: true`
2. Visit `/copilot` — the Insights and Chat tabs should render
3. The Bot icon should appear in the dashboard header
4. Submit a test query and verify the feedback form appears

> **Note:** Enabling via `NEXT_PUBLIC_FEATURE_AI_COPILOT=true` without backend confirmation will NOT activate the copilot. Both gates must pass.

---

## 5. Testing checklist before declaring production-ready

- [ ] Copilot responds correctly in English and Arabic
- [ ] Response latency P95 < 5 seconds
- [ ] Telemetry dashboard shows real data (not zeros)
- [ ] Feedback endpoint stores and returns ratings
- [ ] Branching conversations persist across page reloads
- [ ] Copilot does not leak data between tenants
- [ ] Rate limiting triggers for >100 requests/minute per user
- [ ] Copilot gracefully degrades when LLM is unavailable (fallback message)

---

## 6. Rollback instructions

To disable the copilot:

1. Remove or comment out `NEXT_PUBLIC_FEATURE_AI_COPILOT=true` from `.env.local`
2. Set `FEATURE_AI_COPILOT=false` in `salesos/.env`
3. Rebuild and restart:

```bash
cd salesos
docker compose down
docker compose up -d --build
```

After rollback:
- Copilot nav button and panel disappear from the dashboard
- `/copilot` route shows the "disabled" honesty screen
- All product endpoints return 403

---

## 7. References

| Document | Path |
|----------|------|
| AI Honesty Statement | `docs/audit/ga-engineering-audit/AI_HONESTY.md` |
| Production Plan (Waves 6–7) | `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` |
| Executive Summary (NO-GO) | `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` |
| Copilot Router | `salesos/backend/app/routers/copilot.py` |
| Config (flag) | `salesos/backend/app/config.py:150` |
| FE Activation Hook | `salesos/frontend/src/lib/hooks/useAiCopilotEnabled.ts` |
| Dashboard Layout (UI gate) | `salesos/frontend/src/app/(dashboard)/layout.tsx` |
