import { useState, useEffect } from 'react'
import { fetchConfig, createSession } from './api'
import { ChatWidget } from './ChatWidget'

interface WidgetProps {
  apiKey: string
  gatewayUrl?: string
}

type State =
  | { status: 'idle' }
  | { status: 'loading'; workspaceName?: string }
  | { status: 'error'; message: string }
  | { status: 'open'; workspaceName: string; sessionId: string }

export function Widget({ apiKey }: WidgetProps) {
  const [open, setOpen] = useState(false)
  const [state, setState] = useState<State>({ status: 'idle' })

  // Pre-load config + session on mount so opening is instant
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const config = await fetchConfig(apiKey)
        if (cancelled) return
        const session = await createSession(apiKey)
        if (cancelled) return
        setState({ status: 'open', workspaceName: config.workspace_name, sessionId: session.id })
        // Keep closed until user clicks launcher
        setOpen(false)
      } catch (err: any) {
        if (!cancelled) setState({ status: 'error', message: err.message })
      }
    }
    setState({ status: 'loading' })
    init()
    return () => { cancelled = true }
  }, [apiKey])

  const handleLauncherClick = () => {
    if (state.status === 'open') setOpen((v) => !v)
  }

  return (
    <div className="dm-widget">
      {/* Chat panel */}
      {open && state.status === 'open' && (
        <ChatWidget
          apiKey={apiKey}
          sessionId={state.sessionId}
          workspaceName={state.workspaceName}
          onClose={() => setOpen(false)}
        />
      )}

      {/* Launcher button */}
      <button
        className="dm-launcher"
        onClick={handleLauncherClick}
        disabled={state.status === 'loading'}
        aria-label="Open chat"
        title={state.status === 'error' ? state.message : 'Chat with us'}
      >
        {open ? (
          /* X icon */
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          /* Chat bubble icon */
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>
    </div>
  )
}
