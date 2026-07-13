# Frontend Engineer — SalesOS

> SalesOS Engineering Team · Saudi Arabia (Remote OK)

---

## About SalesOS

SalesOS is an AI-native enterprise intelligence platform. Our frontend is built with Next.js 15, React 19, TypeScript, and Tailwind CSS 4 — serving dashboards, decision widgets, pipeline views, and CRM interfaces. We operate a Widget SDK (v1.0 frozen) that enables modular, testable widget development with contract tests.

## Role

You will build and maintain the SalesOS web application — dashboard layouts, domain-specific widgets, real-time data visualizations, and Arabic/English bilingual interfaces. You will work with our frozen Widget SDK to create new widgets and maintain existing ones.

## Requirements

### Must-Have

- **React 19** — hooks, server components, concurrent features, Suspense
- **Next.js 15** — App Router, server actions, middleware, route handlers
- **TypeScript** — strict mode, generics, utility types, zero `any` in production code
- **Tailwind CSS 4** — utility-first styling, design tokens, responsive design
- **RTL support** — bidirectional layouts, CSS logical properties, Arabic text handling
- **Testing** — Jest, React Testing Library, component testing patterns

### Nice-to-Have

- **Widget SDK experience** — or similar widget/plugin architecture patterns
- **Data visualization** — charts, dashboards, real-time updates
- **Accessibility** — WCAG AA compliance, keyboard navigation, ARIA attributes
- **Performance** — Core Web Vitals optimization, code splitting, lazy loading
- **Storybook** — component documentation and visual testing

## Architecture Context

| Principle | Implementation |
|-----------|---------------|
| Widget SDK v1.0 | Frozen — `createWidget()`, `createDashboardWidget()`, contract tests |
| Container/View Pattern | Container manages SDK state, View is pure presentation |
| No Dashboard Context in Views | Views receive props only, no direct context access |
| Dark Mode | CSS variables with automatic dark/light switching |
| RTL Default | Arabic-first layout with LTR support |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| UI Library | React 19 |
| Language | TypeScript 5 (strict) |
| Styling | Tailwind CSS 4 + CSS variables |
| State | React Context + SWR/React Query |
| Testing | Jest + React Testing Library |
| Components | @salesos/ui + Foundation Components |
| Design Tokens | @salesos/design-language |
| Linting | ESLint, Prettier |

## Responsibilities

1. Build and maintain Next.js pages and components
2. Develop widgets using the frozen Widget SDK
3. Implement responsive layouts with RTL support
4. Create accessible, WCAG AA compliant interfaces
5. Write component tests and contract tests
6. Optimize bundle size and Core Web Vitals
7. Collaborate with backend engineers on API contracts
8. Maintain design system tokens and component library

## Widget SDK Context

The SalesOS Widget SDK v1.0 is **frozen** (ADR-003). You will build widgets using:

```typescript
// Dashboard widget
const MyWidget = createDashboardWidget({
  id: 'my-widget',
  component: MyComponent,
  permissions: ['read:companies'],
  featureFlags: ['new-ui'],
});

// Contract test
describeWidgetContract('My Widget', MyWidget, {
  requiredPermissions: ['read:companies'],
  expectedFeatures: ['data-loading', 'error-handling'],
});
```

## What We Offer

- Build on a stable, frozen SDK — no churn, predictable development
- Modern stack: Next.js 15, React 19, TypeScript strict, Tailwind 4
- Bilingual platform (Arabic + English) with proper RTL support
- Widget-based architecture — clear boundaries, testable components
- Competitive compensation aligned with Saudi market

## Interview Process

1. **Technical Screening** — React + TypeScript coding challenge (1 hour)
2. **Widget Building** — Build a small widget using SDK patterns (take-home, 2 hours max)
3. **Architecture Discussion** — Widget SDK, Container/View pattern, accessibility (45 min)
4. **Team Fit** — Meet the engineering team (30 min)
5. **Offer** — Within 48 hours of final interview

---

*SalesOS is an equal opportunity employer. We value diversity and inclusion.*
