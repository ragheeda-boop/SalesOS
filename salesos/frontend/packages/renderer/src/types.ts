export interface UISchema {
  schemaVersion: string
  entityType: string
  entityId: string
  title?: string
  tabs: UISchemaTab[]
  actions?: UIAction[]
  context?: Record<string, unknown>
}

export interface UISchemaTab {
  id: string
  title: string
  icon?: string
  sections: UISchemaSection[]
  widgetIds?: string[]
}

export interface UISchemaSection {
  id: string
  title?: string
  columns?: number
  widgets?: UIWidget[]
  nodes?: UISchemaNode[]
}

export interface UIWidget {
  widgetId: string
  widgetType: string
  title?: string
  size?: 'small' | 'medium' | 'large' | 'full'
  props?: Record<string, unknown>
  config?: Record<string, unknown>
}

export interface UISchemaNode {
  type: 'text' | 'badge' | 'metric' | 'link' | 'list' | 'table'
  label?: string
  value?: unknown
  children?: UISchemaNode[]
  props?: Record<string, unknown>
}

export interface UIAction {
  id: string
  label: string
  icon?: string
  variant?: 'primary' | 'secondary' | 'outline' | 'danger'
  handler?: string
  confirmation?: string
}
