export const UX_PRINCIPLES = {
  searchable: {
    id: 'rule-01',
    rule: 'Everything searchable',
    description: 'Every entity, action, setting, and screen must be reachable via search. No deep nesting without search access.',
  },
  linkable: {
    id: 'rule-02',
    rule: 'Everything linkable',
    description: 'Every object, widget, card, and row must have a permanent URL. Users should be able to share and bookmark any state.',
  },
  explainable: {
    id: 'rule-03',
    rule: 'Everything explainable',
    description: 'Every metric, recommendation, and AI decision must provide a human-readable explanation of how it was derived.',
  },
  auditable: {
    id: 'rule-04',
    rule: 'Everything auditable',
    description: 'Every action, change, and decision must be logged with who, what, when, and why. Full audit trail accessible from any object.',
  },
  actionable: {
    id: 'rule-05',
    rule: 'Everything actionable',
    description: 'Every screen must have at least one primary action. No passive views. Every insight must lead to an action.',
  },
  contextual: {
    id: 'rule-06',
    rule: 'Everything contextual',
    description: 'UI must adapt based on user role, permissions, recent activity, and current workspace. No one-size-fits-all screens.',
  },
  composable: {
    id: 'rule-07',
    rule: 'Everything composable',
    description: 'Every widget, card, and action must be rearrangeable, resizable, and hideable. Users build their own workspace.',
  },
  noEmpty: {
    id: 'rule-08',
    rule: 'Never show empty pages',
    description: 'Every empty state must offer a next action: import, create, connect, or learn. Never show blank screens or empty tables.',
  },
  aiAlways: {
    id: 'rule-09',
    rule: 'AI is always available',
    description: 'Every widget, card, and text selection must have an AI action available. AI is a layer, not a separate page.',
  },
  oneClick: {
    id: 'rule-10',
    rule: 'One click to the next action',
    description: 'The most likely next action must always be one click away. Minimize navigation depth to 2 levels maximum.',
  },
} as const

export type UXPrinciple = keyof typeof UX_PRINCIPLES
