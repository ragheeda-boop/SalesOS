"use client"

import { type ComponentType, type ReactNode } from "react"
import { createWidget } from "@/features/dashboard/sdk"
import type { WidgetConfig, WidgetRenderContext } from "@/features/dashboard/sdk/types"

interface WorkspaceWidgetAdapterOptions<T> {
  metadata: {
    id: string
    title: string
    description?: string
    gridColumn?: string
    minHeight?: string
    refreshInterval?: number
    staleThreshold?: number
  }
  useData: () => {
    data: T | null
    status: "ready" | "loading" | "degraded" | "error"
    lastUpdated: string | null
    error: Error | null
    refetch: () => void
  }
  render: (ctx: WidgetRenderContext<T>) => ReactNode
  fallback?: ReactNode
}

export function createWorkspaceDashboardAdapter<T>(
  options: WorkspaceWidgetAdapterOptions<T>
): ComponentType {
  return createWidget<T>({
    metadata: {
      id: options.metadata.id,
      title: options.metadata.title,
      description: options.metadata.description,
      gridColumn: options.metadata.gridColumn,
      minHeight: options.metadata.minHeight,
      refreshInterval: options.metadata.refreshInterval,
      staleThreshold: options.metadata.staleThreshold,
    } as WidgetConfig<T>["metadata"],
    useData: options.useData,
    render: options.render,
    fallback: options.fallback,
  })
}

export function wrapWorkspaceWidget<T>(
  workspaceWidgetFactory: (config: { metadata: Record<string, unknown>; useData: () => T; render: (ctx: T) => ReactNode }) => ComponentType,
  dashboardMetadata: WorkspaceWidgetAdapterOptions<T>["metadata"],
  useData: WorkspaceWidgetAdapterOptions<T>["useData"],
  render: WorkspaceWidgetAdapterOptions<T>["render"]
): ComponentType {
  return createWorkspaceDashboardAdapter({
    metadata: dashboardMetadata,
    useData,
    render,
  })
}
