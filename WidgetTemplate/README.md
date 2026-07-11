# Widget Template

> قالب جاهز لبدء أي Widget جديدة في SalesOS Dashboard.

## Usage

```bash
# 1. Copy the template
cp -r WidgetTemplate/ src/features/dashboard/widgets/your-widget/

# 2. Rename files (replace "YourWidget" with your widget name)
mv YourWidgetContainer.tsx YourWidgetContainer.tsx
mv YourWidgetView.tsx YourWidgetView.tsx

# 3. Update types.ts with your data shape
# 4. Update YourWidgetContainer.tsx with your metadata
# 5. Update YourWidgetView.tsx with your UI
# 6. Update test with your data
# 7. Register in _registry/widget-config.ts
```

## Files

| File | Purpose |
|------|---------|
| `index.ts` | Barrel export |
| `YourWidgetContainer.tsx` | Container — uses `createDashboardWidget()`, defines metadata |
| `YourWidgetView.tsx` | View — pure component, no SDK dependency |
| `types.ts` | Props and data types |
| `__tests__/YourWidget.test.tsx` | Contract tests + unit tests (edit with your data) |

## Checklist

- [ ] Update metadata (title, description, permissions, featureFlag)
- [ ] Register in `_registry/widget-config.ts`
- [ ] Update `render()` with your View
- [ ] Edit test data to match your type
- [ ] Run `npx jest --no-coverage` to verify
- [ ] Refer to `docs/REFERENCE_WIDGET_GUIDE.md` for full standards

## Standards Reference

راجع `docs/REFERENCE_WIDGET_GUIDE.md` للحصول على القائمة الكاملة لمتطلبات Widget:
- Definition of Done (12 item)
- Accessibility Checklist (10 items)
- Testing Contract (18+ tests)
- Performance Guidelines
- Anti-patterns
