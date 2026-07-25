// Workspace Schema & Renderer (v5)
export { generateWorkspace, type WorkspaceConfig, type CapabilityDefinition, type EntityType } from './generator'
export { WORKSPACE_PRESETS, getPreset, getAllPresets, type WorkspaceRole, type WorkspacePreset, type WidgetPreset } from './presets'
export { WorkspaceRenderer, type WorkspaceRendererProps } from './renderer'

// Workspace Components
export { GlobalActivityFeed, type ActivityEvent, type ActivityType, type ActivityEntity } from './global-activity-feed'
export { UniversalInbox, type InboxItem, type InboxItemType } from './universal-inbox'
export { RevenueCommandCenter, type RevenueMetrics } from './revenue-command-center'
export { AIOperatingAssistant, type WorkflowExecution, type WorkflowStep, type QuickAction } from './ai-operating-assistant'

// Workspace types (unique to workspace, not part of canonical SDK)
export type { WorkspaceWidgetEntry, WorkspaceContextValue } from './workspace-types'

// Workspace Infrastructure
export { deriveStatus } from './derive-status'
export { createWorkspaceProvider } from './workspace-provider'
export { WorkspaceGrid, type WorkspaceGridProps } from './workspace-grid'
export { WorkspaceErrorBoundary } from './workspace-error-boundary'
export { WorkspaceLoading, type WorkspaceLoadingProps } from './workspace-loading'
export { createRegistry, type RegistryEntry } from './workspace-registry'
export { createWorkspaceWidget, type WorkspaceWidgetConfig } from './create-workspace-widget'
