// Workspace Schema & Renderer (v5)
export { generateWorkspace, type WorkspaceConfig, type CapabilityDefinition, type EntityType } from './generator'
export { WORKSPACE_PRESETS, getPreset, getAllPresets, type WorkspaceRole, type WorkspacePreset, type WidgetPreset } from './presets'
export { WorkspaceRenderer, type WorkspaceRendererProps } from './renderer'

// Workspace Components
export { GlobalActivityFeed, type ActivityEvent, type ActivityType, type ActivityEntity } from './global-activity-feed'
export { UniversalInbox, type InboxItem, type InboxItemType } from './universal-inbox'
export { RevenueCommandCenter, type RevenueMetrics } from './revenue-command-center'
export { AIOperatingAssistant, type WorkflowExecution, type WorkflowStep, type QuickAction } from './ai-operating-assistant'

// Widget SDK (generic, extracted from Dashboard Widget SDK v1.0)
export { createWidget } from './create-widget'
export { useWidgetLifecycle } from './widget-lifecycle'
export { widgetTelemetry, type TelemetryEventType, type TelemetryEvent } from './widget-telemetry'
export { setPermissionChecker, checkPermissions, type PermissionChecker } from './widget-permissions'
export { setFeatureFlagResolver, isFeatureEnabled, type FeatureFlagResolver } from './widget-feature-flags'
export type {
  WidgetStatus,
  WidgetPriority,
  WidgetCategory,
  WidgetFeatureTier,
  WidgetFeatureFlag,
  WidgetMetadata,
  WidgetLifecycle,
  WidgetData,
  WidgetRenderContext,
  WidgetConfig,
  WorkspaceWidgetEntry,
  WorkspaceContextValue,
} from './types'

// Workspace Infrastructure
export { deriveStatus } from './derive-status'
export { createWorkspaceProvider } from './workspace-provider'
export { WorkspaceGrid, type WorkspaceGridProps } from './workspace-grid'
export { WorkspaceErrorBoundary } from './workspace-error-boundary'
export { WorkspaceLoading, type WorkspaceLoadingProps } from './workspace-loading'
export { createRegistry, type RegistryEntry } from './workspace-registry'
export { createWorkspaceWidget, type WorkspaceWidgetConfig } from './create-workspace-widget'
