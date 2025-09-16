import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/features/chat/types'
import { CitationPanel } from './CitationPanel'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[75%]', isUser ? '' : 'w-full')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {!isUser && message.citations.length > 0 && (
          <CitationPanel citations={message.citations} />
        )}
      </div>
    </div>
  )
}
