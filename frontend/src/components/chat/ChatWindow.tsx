import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useChatHistory } from '@/features/chat/hooks'
import { useSSE } from '@/hooks/useSSE'
import type { ChatMessage, SSECitation } from '@/features/chat/types'
import { MessageBubble } from './MessageBubble'
import { StreamingMessage } from './StreamingMessage'
import { ChatInput } from './ChatInput'
import { Spinner } from '@/components/ui/Spinner'

interface ChatWindowProps {
  workspaceId: string
  sessionId: string
}

export function ChatWindow({ workspaceId, sessionId }: ChatWindowProps) {
  const qc = useQueryClient()
  const bottomRef = useRef<HTMLDivElement>(null)
  const { data: history, isLoading } = useChatHistory(workspaceId, sessionId)

  const { streaming, streamingText, send } = useSSE({
    onDone: (_text, _citations) => {
      // Refresh history so the saved assistant message appears
      qc.invalidateQueries({ queryKey: ['chat-history', workspaceId, sessionId] })
    },
  })

  // Scroll to bottom when messages change or streaming text updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history?.messages, streamingText])

  const handleSend = async (content: string) => {
    // Optimistically add user message to the displayed list
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      workspace_id: workspaceId,
      role: 'user',
      content,
      token_count: 0,
      created_at: new Date().toISOString(),
      citations: [],
    }

    qc.setQueryData(
      ['chat-history', workspaceId, sessionId],
      (old: { session: unknown; messages: ChatMessage[] } | undefined) =>
        old ? { ...old, messages: [...old.messages, tempUserMsg] } : old
    )

    await send(`/api/v1/workspaces/${workspaceId}/chat/sessions/${sessionId}/messages`, {
      content,
    })
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    )
  }

  const messages = history?.messages ?? []

  return (
    <div className="flex h-full flex-col">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 && !streaming ? (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            Ask a question about your documents.
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {streaming && <StreamingMessage text={streamingText} />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-2xl">
          <ChatInput onSend={handleSend} disabled={streaming} />
        </div>
      </div>
    </div>
  )
}
