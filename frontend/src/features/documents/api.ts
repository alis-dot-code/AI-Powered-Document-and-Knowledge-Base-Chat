import api from '@/lib/axios'
import type { Document, DocumentStatusResponse, ScrapeUrlRequest } from './types'

export const documentsApi = {
  upload: (workspaceId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Document>(`/workspaces/${workspaceId}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  scrape: (workspaceId: string, data: ScrapeUrlRequest) =>
    api.post<Document>(`/workspaces/${workspaceId}/documents/scrape`, data),

  list: (workspaceId: string, params?: { offset?: number; limit?: number }) =>
    api.get<Document[]>(`/workspaces/${workspaceId}/documents`, { params }),

  get: (workspaceId: string, documentId: string) =>
    api.get<Document>(`/workspaces/${workspaceId}/documents/${documentId}`),

  getStatus: (workspaceId: string, documentId: string) =>
    api.get<DocumentStatusResponse>(
      `/workspaces/${workspaceId}/documents/${documentId}/status`
    ),

  update: (workspaceId: string, documentId: string, title: string) =>
    api.patch<Document>(`/workspaces/${workspaceId}/documents/${documentId}`, { title }),

  delete: (workspaceId: string, documentId: string) =>
    api.delete(`/workspaces/${workspaceId}/documents/${documentId}`),

  reprocess: (workspaceId: string, documentId: string) =>
    api.post<DocumentStatusResponse>(
      `/workspaces/${workspaceId}/documents/${documentId}/reprocess`
    ),
}
