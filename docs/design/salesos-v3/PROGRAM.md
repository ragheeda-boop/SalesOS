# SalesOS Design Program v3

> **Status:** Active program charter  
> **Product:** SalesOS  
> **Validation:** documentation / light validated — **not** Production GO  
> **AI honesty:** Preview / flag-gated until evidence — see [AI_HONESTY.md](../../audit/ga-engineering-audit/AI_HONESTY.md)

## Stance (locked)

1. Do **not** polish the legacy UI in place. Legacy App Router is a **migration source**.
2. **Program > pages:** engines before screen chrome.
3. **Object Model before wireframes.**
4. Navigation depth ≤ **3 clicks** (Workspace → Domain → Object).
5. AI-native UX; **evidence-gated GA**.
6. Never claim Production GO from design docs alone.
7. Visual bar: Linear / Attio / Stripe / Notion density / HubSpot IA depth.

## Roadmap

```text
Research → Architecture → Design System → Engines → Shell
  → Dashboards → Objects → Modules → AI
  → Prototype → Usability → Frontend → Migration → Release
```

| Phase | Name | Index |
|------:|------|-------|
| -1 | Research | [research/](./research/) |
| 0 | Architecture | [architecture/](./architecture/) |
| 1 | Design System | [design-system/](./design-system/) |
| 2 | Engines | [engines/](./engines/) |
| 3 | Shell + Auth | [screens/shell/](./screens/shell/) · [screens/auth/](./screens/auth/) |
| 4 | Dashboards | [screens/dashboards/](./screens/dashboards/) |
| 5 | Objects | [screens/objects/](./screens/objects/) |
| 6 | Modules | [screens/modules/](./screens/modules/) |
| 7 | AI Experience | [ai/ai-experience.md](./ai/ai-experience.md) |
| 8 | Prototype + Usability | [delivery/usability-plan.md](./delivery/usability-plan.md) |
| 9 | Frontend | [frontend/](./frontend/) |
| 10 | Migration + Design Ops + Release | [delivery/](./delivery/) · [design-ops/](./design-ops/) |

## Success metrics

See [delivery/success-metrics.md](./delivery/success-metrics.md).

## Enterprise UX review

- Brief (AR+EN, 1 page): [delivery/DESIGN_REVIEW_BRIEF.md](./delivery/DESIGN_REVIEW_BRIEF.md)
- Checklist: [delivery/enterprise-ux-review.md](./delivery/enterprise-ux-review.md) — **UNSIGNED** (not Production GO).

| Role | Signature | Date | GO / NO-GO |
|------|-----------|------|------------|
| Design Lead | ________________ | ____ | ________ |
| CTO | ________________ | ____ | ________ |
| Product | ________________ | ____ | ________ |

## Related

- Legacy page map: [PAGE_MAP_SALESOS.md](../../audit/ga-engineering-audit/PAGE_MAP_SALESOS.md)
- Prior strategy (superseded as governing program): [DESIGN_STRATEGY.md](../../vnext/DESIGN_STRATEGY.md)
