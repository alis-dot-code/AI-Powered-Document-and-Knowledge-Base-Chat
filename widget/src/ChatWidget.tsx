import { useState, useRef, useEffect, useCallback } from 'react'
import { sendMessage } from './api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

interface ChatWidgetProps {
  apiKey: string
  sessionId: string
  workspaceName: string
  onClose: () => void
}

export function ChatWidget({ apiKey, sessionId, workspaceName, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    const assistantId = crypto.randomUUID()
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: 'assistant', content: '', streaming: true },
    ])
    setStreaming(true)

    abortRef.current = new AbortController()
    await sendMessage(
      apiKey,
      sessionId,
      text,
      {
        onToken: (chunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + chunk } : m
            )
          )
        },
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, streaming: false } : m
            )
          )
          setStreaming(false)
        },
        onError: (msg) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `⚠ ${msg}`, streaming: false }
                : m
            )
          )
          setStreaming(false)
        },
      },
      abortRef.current.signal,
    )
  }, [apiKey, sessionId, input, streaming])

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="dm-widget">
      <div className="dm-panel">
        {/* Header */}
        <div className="dm-header">
          <span className="dm-header-title">💬 {workspaceName}</span>
          <button className="dm-close-btn" onClick={onClose} aria-label="Close chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="dm-messages">
          {messages.length === 0 && (
            <p style={{ fontSize: 12, color: '#9ca3af', textAlign: 'center', marginTop: 24 }}>
              Ask anything about our docs…
            </p>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`dm-msg dm-msg--${msg.role}`}>
              <div className="dm-bubble">
                {msg.content || (msg.streaming ? (
                  <div className="dm-typing">
                    <div className="dm-dot" />
                    <div className="dm-dot" />
                    <div className="dm-dot" />
                  </div>
                ) : null)}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="dm-input-row">
          <textarea
            className="dm-input"
            rows={1}
            placeholder="Ask a question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={streaming}
          />
          <button
            className="dm-send-btn"
            onClick={send}
            disabled={streaming || !input.trim()}
            aria-label="Send"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        <div className="dm-footer">
          Powered by <a href="https://docmind.ai" target="_blank" rel="noopener noreferrer">DocMind</a>
        </div>
      </div>
    </div>
  )
}
