import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './api'

export function useSessions(workspaceId: string) {
  return useQuery({
    queryKey: ['sessions', workspaceId],
    queryFn: () => chatApi.listSessions(workspaceId).then((r) => r.data),
    enabled: !!workspaceId,
  })
}

export function useChatHistory(workspaceId: string, sessionId: string) {
  return useQuery({
    queryKey: ['chat-history', workspaceId, sessionId],
    queryFn: () => chatApi.getHistory(workspaceId, sessionId).then((r) => r.data),
    enabled: !!workspaceId && !!sessionId,
  })
}

export function useCreateSession(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (title?: string) => chatApi.createSession(workspaceId, title).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions', workspaceId] }),
  })
}

export function useDeleteSession(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(workspaceId, sessionId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions', workspaceId] }),
  })
}

export function useRenameSession(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, title }: { sessionId: string; title: string }) =>
      chatApi.updateSession(workspaceId, sessionId, title).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions', workspaceId] }),
  })
}
