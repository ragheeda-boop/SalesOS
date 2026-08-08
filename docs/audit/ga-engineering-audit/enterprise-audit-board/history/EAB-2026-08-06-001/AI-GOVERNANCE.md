# AI Governance — EAB-2026-08-06-001 (Axis 43)

**Separate from Security (Axis 30).**  
**Align with:** [AI_HONESTY.md](../../../AI_HONESTY.md)  
**Validation:** light validated

---

## Hard-cap checks

| Gate | Status | Effect |
|------|--------|--------|
| `feature_ai_copilot` default False | **Pass** (`config.py` L150) | ≤29 hard-cap **not** triggered |
| FE Decision STUB marketed as live GA | **Not observed** in SoT docs/code reviewed | ≤29 hard-cap **not** triggered |
| Consequential AI without Human Override | **Partial** (accept/execute/feedback exist; not universal HITL) | Soft pressure toward ≤49 overall |

---

## Sub-factor scores

| Sub-factor | Score | Notes |
|------------|------:|-------|
| AI Safety | 55 | Policies/studio exist; product gated off by default |
| Explainability | 40 | Split explain / reasoning / audit across engines |
| Auditability | 65 | `AIAuditService` + admin AI audit UI present |
| Prompt Governance | 35 | ≥3 registries; studio prompt library experimental |
| Tool Governance | 25 | Agent tools placeholder / empty search |
| Memory Governance | 30 | Studio ai-memory tip / in-memory honesty |
| Human Override | 45 | Decision accept/execute/feedback; merge HITL; not platform-wide |
| Decision Transparency | 30 | Multi-engine + route collisions |
| Model Independence | 35 | Multi-provider code; OpenAI default path |
| Vendor Lock-in | 30 | OpenAI key/model gravity; fake chaos failover |
| Honesty gates | **Pass** | Flag False + STUB labeled + 403 when off |

```text
AIGOV = mean(55,40,65,35,25,30,45,30,35,30) = 39
```

**Axis 43 score: ~39** (light validated)

---

## What may / may not be claimed

**Allowed:** experimental AI behind flags; Decision Center HTTP as operational (not “AI-native GA”).  
**Forbidden:** AI-native GA; 98% AI PASS; autonomous agents in production; multi-product intelligence GA from this repo.

---

*AI Governance — EAB-2026-08-06-001*
