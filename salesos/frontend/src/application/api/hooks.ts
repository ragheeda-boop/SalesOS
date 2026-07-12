'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTenantId } from '@/lib/hooks/useTenant'
import type { RevenueOpportunity, OpportunityStage } from '../revenue-execution/opportunity.dto'

interface CreateOpportunityInput {
  name: string
  companyId: string
  companyName: string
  source?: string
  estimatedValue: number
  confidence?: number
  stage?: OpportunityStage
}

interface CreateTaskInput {
  title: string
  priority?: string
  company_id?: string
  assignee_id?: string
}

const API = '/api/v1'

export function useOpportunities(stage?: string) {
  const params = stage ? `?stage=${stage}` : ''
  return useQuery({
    queryKey: ['opportunities', stage],
    queryFn: async () => {
      const res = await fetch(`${API}/opportunities${params}`, { headers: { 'X-Tenant-Id': getTenantId() } })
      if (!res.ok) throw new Error('Failed to load opportunities')
      return res.json()
    },
    staleTime: 30_000,
  })
}

export function useCreateOpportunity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateOpportunityInput) => {
      const res = await fetch(`${API}/opportunities`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': getTenantId() },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to create opportunity')
      return res.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['opportunities'] }),
  })
}

export function useUpdateOpportunityStage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, stage }: { id: string; stage: OpportunityStage }) => {
      const res = await fetch(`${API}/opportunities/${id}/stage`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': getTenantId() },
        body: JSON.stringify({ stage }),
      })
      if (!res.ok) throw new Error('Failed to update stage')
      return res.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['opportunities'] }),
  })
}

export function useTasks(priority?: string) {
  const params = priority ? `?priority=${priority}` : ''
  return useQuery({
    queryKey: ['tasks', priority],
    queryFn: async () => {
      const res = await fetch(`${API}/tasks${params}`, { headers: { 'X-Tenant-Id': getTenantId() } })
      if (!res.ok) throw new Error('Failed to load tasks')
      return res.json()
    },
    staleTime: 30_000,
  })
}

export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateTaskInput) => {
      const res = await fetch(`${API}/tasks`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': getTenantId() },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to create task')
      return res.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function useCompleteTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API}/tasks/${id}/complete`, {
        method: 'PUT', headers: { 'X-Tenant-Id': getTenantId() },
      })
      if (!res.ok) throw new Error('Failed to complete task')
      return res.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function usePipeline() {
  return useQuery({
    queryKey: ['pipeline'],
    queryFn: async () => {
      const res = await fetch(`${API}/pipeline`, { headers: { 'X-Tenant-Id': getTenantId() } })
      if (!res.ok) throw new Error('Failed to load pipeline')
      return res.json()
    },
    staleTime: 30_000,
  })
}
