import { useState } from 'react'
import { Plus, Trash2, MessageSquare } from 'lucide-react'
import { useGlobalStore } from '@/stores/global'
import { useSessions, useCreateSession, useDeleteSession } from '@/features/chat/hooks'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

export function ChatPage() {
  const { activeWorkspaceId } = useGlobalStore()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)

  const { data: sessions, isLoading } = useSessions(activeWorkspaceId ?? '')
  const createSession = useCreateSession(activeWorkspaceId ?? '')
  const deleteSession = useDeleteSession(activeWorkspaceId ?? '')

  if (!activeWorkspaceId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        Select a workspace to start chatting.
      </div>
    )
  }

  const handleNewSession = async () => {
    const session = await createSession.mutateAsync()
    setActiveSessionId(session.id)
  }

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (!confirm('Delete this chat?')) return
    await deleteSession.mutateAsync(sessionId)
    if (activeSessionId === sessionId) setActiveSessionId(null)
  }

  return (
    <div className="flex h-full">
      {/* Session sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b border-gray-100 px-3 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Chats
          </span>
          <button
            onClick={handleNewSession}
            disabled={createSession.isPending}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
            title="New chat"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex justify-center py-6">
              <Spinner />
            </div>
          ) : !sessions?.length ? (
            <p className="py-6 text-center text-xs text-gray-400">No chats yet.</p>
          ) : (
            <ul className="flex flex-col gap-0.5">
              {sessions.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => setActiveSessionId(s.id)}
                    className={cn(
                      'group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs transition-colors',
                      activeSessionId === s.id
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    )}
                  >
                    <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                    <span className="flex-1 truncate">{s.title}</span>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => handleDelete(e, s.id)}
                      onKeyDown={(e) => e.key === 'Enter' && handleDelete(e as unknown as React.MouseEvent, s.id)}
                      className="hidden rounded p-0.5 text-gray-400 hover:text-red-500 group-hover:block"
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeSessionId ? (
          <ChatWindow workspaceId={activeWorkspaceId} sessionId={activeSessionId} />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-gray-400">
            <MessageSquare className="h-10 w-10 text-gray-300" />
            <p className="text-sm">Select a chat or start a new one.</p>
            <Button size="sm" onClick={handleNewSession} loading={createSession.isPending}>
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
