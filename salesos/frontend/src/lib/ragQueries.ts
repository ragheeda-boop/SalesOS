"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import { getTenantId } from "./hooks/useTenant"

export type DocumentSourceType = "email" | "meeting" | "note"

export interface RagDocument {
  id: string
  title: string
  content: string
  source_type: DocumentSourceType
  created_at: string
}

export interface RagAnswer {
  answer: string
  citations: { source: string; text: string; relevance: number }[]
}

export const ragKeys = {
  all: ["rag"] as const,
  documents: () => [...ragKeys.all, "documents"] as const,
  document: (id: string) => [...ragKeys.documents(), id] as const,
  answer: (question: string) => [...ragKeys.all, "answer", question] as const,
}

export function useRagDocuments() {
  return useQuery({
    queryKey: ragKeys.documents(),
    queryFn: async () => {
      const res = await api.get("/api/v1/rag/documents", {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as RagDocument[]
    },
    staleTime: 15_000,
  })
}

export function useAskQuestion() {
  return useMutation({
    mutationFn: async (question: string) => {
      const res = await api.post("/api/v1/rag/ask", { question }, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as RagAnswer
    },
  })
}

export function useIngestDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: { title: string; content: string; source_type: DocumentSourceType }) => {
      const res = await api.post("/api/v1/rag/documents", data, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
      return res.data as RagDocument
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ragKeys.documents() }),
  })
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/rag/documents/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ragKeys.documents() }),
  })
}
