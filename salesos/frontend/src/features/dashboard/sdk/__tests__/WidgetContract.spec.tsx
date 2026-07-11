import { describeWidgetContract } from '../testing/WidgetContract'

describeWidgetContract({
  name: 'TestWidget',
  defaultData: { value: 42 },
  config: {
    metadata: {
      id: 'test-widget',
      title: 'Test Widget',
      minHeight: '200px',
      permissions: ['test:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => <div role="region">{data.value}</div>,
  },
})
