import api from '@/lib/axios'
import type { ChatSession, ChatHistoryResponse } from './types'

const base = (workspaceId: string) => `/workspaces/${workspaceId}/chat`

export const chatApi = {
  createSession: (workspaceId: string, title?: string) =>
    api.post<ChatSession>(`${base(workspaceId)}/sessions`, { title: title ?? 'New Chat' }),

  listSessions: (workspaceId: string) =>
    api.get<ChatSession[]>(`${base(workspaceId)}/sessions`),

  getSession: (workspaceId: string, sessionId: string) =>
    api.get<ChatSession>(`${base(workspaceId)}/sessions/${sessionId}`),

  updateSession: (workspaceId: string, sessionId: string, title: string) =>
    api.patch<ChatSession>(`${base(workspaceId)}/sessions/${sessionId}`, { title }),

  deleteSession: (workspaceId: string, sessionId: string) =>
    api.delete(`${base(workspaceId)}/sessions/${sessionId}`),

  getHistory: (workspaceId: string, sessionId: string) =>
    api.get<ChatHistoryResponse>(`${base(workspaceId)}/sessions/${sessionId}/messages`),
}
