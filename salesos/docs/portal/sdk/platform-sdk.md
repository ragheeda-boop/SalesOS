# Platform Kernel SDK Reference

> **نواة المنصة — القياس عن بعد، الصلاحيات، أعلام الميزات، التخزين المؤقت**

Package: `@salesos/platform` | Status: **Active** | Version: v0.9.0

The Platform Kernel provides shared runtime services used by all SalesOS SDKs and applications.

---

## Installation

```bash
npm install @salesos/platform
```

---

## Platform Bootstrap

```typescript
import { createPlatform } from '@salesos/platform'
import { TelemetryProvider, PermissionResolver, FeatureFlagResolver } from '@salesos/platform'

const platform = createPlatform({
  permissions: permissionResolver,
  featureFlags: flagResolver,
  telemetry: telemetryProvider,
  cache: cacheProvider,
})

// Initializes: Cache → Config → Telemetry → Permissions → Feature Flags → Events
```

---

## Telemetry

```typescript
import { telemetry } from '@salesos/platform'

// Record a metric
telemetry.record('widget.load_time', 245, { widgetId: 'my-widget' })

// Get summary
const summary = telemetry.summary()
// { 'widget.load_time': { count: 10, avg: 230, min: 150, max: 450 } }

// Flush to pipeline
const events = telemetry.flush()
```

---

## Permissions

```typescript
import { createPermissionResolver } from '@salesos/platform'

const resolver = createPermissionResolver([
  { resource: 'opportunity', action: 'read' },
  { resource: 'nba', action: 'read' },
])

const canRead = resolver.hasPermission('opportunity', 'read')
// → true

const canDelete = resolver.hasPermission('opportunity', 'delete')
// → false
```

---

## Feature Flags

```typescript
import { createFeatureFlagResolver, TieredFeatureFlagResolver } from '@salesos/platform'

// Static resolver
const flags = createFeatureFlagResolver({
  'ff_nba_enabled': true,
  'ff_workflow_automation': false,
})

// Tiered resolver (checks user tier against flag's required tier)
const tieredFlags = new TieredFeatureFlagResolver({
  flags: { 'ff_ai_reasoning': { tier: 'enterprise' } },
  userTier: 'enterprise',
})

tieredFlags.isEnabled('ff_ai_reasoning') // true
```

---

## Cache

```typescript
import { createCache } from '@salesos/platform'

const cache = createCache<string>({ defaultTtl: 300_000 }) // 5 min

await cache.set('key', 'value')
const value = await cache.get('key')

// getOrSet with async factory
const data = await cache.getOrSet('company:123', async () => {
  return await fetchCompanyFromAPI('123')
})
```

---

## Events

```typescript
import { createEventBus } from '@salesos/platform'

const bus = createEventBus()

bus.on('opportunity.stage_changed', (event) => {
  console.log(`Opportunity ${event.data.opportunity_id} moved to ${event.data.new_stage}`)
})

bus.emit({
  type: 'opportunity.stage_changed',
  data: { opportunity_id: 'opp_123', new_stage: 'negotiation' },
})
```

---

## Related

| Resource | Link |
|----------|------|
| Platform Kernel Design | [Kernel Design](../../docs/wave-2/02-PLATFORM_KERNEL_DESIGN.md) |
