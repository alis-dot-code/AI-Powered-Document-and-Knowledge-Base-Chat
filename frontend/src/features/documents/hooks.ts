import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { documentsApi } from './api'
import type { ScrapeUrlRequest } from './types'

export function useDocuments(workspaceId: string) {
  return useQuery({
    queryKey: ['documents', workspaceId],
    queryFn: async () => {
      const { data } = await documentsApi.list(workspaceId)
      return data
    },
    enabled: !!workspaceId,
    refetchInterval: (query) => {
      // Poll while any doc is pending/processing
      const docs = query.state.data
      const hasPending = docs?.some(
        (d) => d.status === 'pending' || d.status === 'processing'
      )
      return hasPending ? 3000 : false
    },
  })
}

export function useDocument(workspaceId: string, documentId: string) {
  return useQuery({
    queryKey: ['documents', workspaceId, documentId],
    queryFn: async () => {
      const { data } = await documentsApi.get(workspaceId, documentId)
      return data
    },
    enabled: !!workspaceId && !!documentId,
  })
}

export function useUploadDocument(workspaceId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => documentsApi.upload(workspaceId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', workspaceId] })
      toast.success('Upload started — processing in background')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Upload failed')
    },
  })
}

export function useScrapeUrl(workspaceId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (data: ScrapeUrlRequest) => documentsApi.scrape(workspaceId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', workspaceId] })
      toast.success('URL queued for scraping')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Scrape failed')
    },
  })
}

export function useDeleteDocument(workspaceId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(workspaceId, documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', workspaceId] })
      toast.success('Document deleted')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Delete failed')
    },
  })
}

export function useReprocessDocument(workspaceId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.reprocess(workspaceId, documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', workspaceId] })
      toast.success('Reprocessing queued')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Reprocess failed')
    },
  })
}
