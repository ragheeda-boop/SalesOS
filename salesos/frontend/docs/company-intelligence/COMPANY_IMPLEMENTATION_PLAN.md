# Company Intelligence Command Center — Implementation Plan

## Phase 1: Architecture Documents (DONE)
- ✅ COMPANY_INTELLIGENCE_ARCHITECTURE.md
- ✅ COMPANY_INTELLIGENCE_BLUEPRINT.md
- ✅ COMPANY_COMPONENT_CATALOG.md
- ✅ COMPANY_API_MAPPING.md
- ✅ COMPANY_IMPLEMENTATION_PLAN.md

## Phase 2: Application Layer
1. `company-intelligence.dto.ts` — Full DTOs for all 10 widgets
2. `company-intelligence.store.ts` — Widget derivation + WidgetMap
3. `company-intelligence.api.ts` — API function
4. `company-intelligence.keys.ts` — Query keys
5. `useCompanyIntelligence.ts` — React Query hook

## Phase 3: Workspace Infrastructure
1. `_providers/company-intelligence-provider.tsx` — Uses `createWorkspaceProvider`
2. `_registry/widget-config.ts` — Config for all 10 widgets
3. `_layout/company-intelligence-layout.tsx` — Grid, Loading, WidgetShell
4. `index.ts` — Public API

## Phase 4: Reference Widget — Company DNA
1. Types
2. View (visual gauge cards for all 20 dimensions)
3. Container (uses `createWidget`)
4. Tests (contract + unit + a11y + interaction)

## Phase 5–13: Widgets 2–10 (in order)
1. AI Recommendation Engine
2. Decision Makers
3. Relationship Graph
4. Smart Timeline
5. Signals Feed
6. Government Intelligence
7. Document Intelligence
8. Buying Journey
9. Golden Record Explorer

## Phase 14: Testing + Quality
1. Every widget: contract test (describeWidgetContract)
2. Every widget: unit tests (states, empty, error, a11y, keyboard)
3. Full workspace integration test
4. Dark mode + RTL verification
5. Accessibility audit
