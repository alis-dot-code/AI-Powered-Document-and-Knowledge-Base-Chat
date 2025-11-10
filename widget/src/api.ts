const GATEWAY = (window as any).DocMindWidget?._gatewayUrl ?? 'http://localhost:3000'

export interface WidgetConfig {
  workspace_name: string
  workspace_id: string
  key_name: string
}

export interface ChatSession {
  id: string
  title: string
}

export async function fetchConfig(apiKey: string): Promise<WidgetConfig> {
  const res = await fetch(`${GATEWAY}/api/v1/widget/config`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  })
  if (!res.ok) throw new Error('Invalid API key')
  return res.json()
}

export async function createSession(apiKey: string): Promise<ChatSession> {
  const res = await fetch(`${GATEWAY}/api/v1/widget/sessions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export interface SSECallbacks {
  onToken: (text: string) => void
  onDone: () => void
  onError: (msg: string) => void
}

export async function sendMessage(
  apiKey: string,
  sessionId: string,
  content: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${GATEWAY}/api/v1/widget/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
    signal,
  })

  if (!res.ok || !res.body) {
    callbacks.onError('Request failed')
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const payload = JSON.parse(line.slice(6))
        if (payload.type === 'token') callbacks.onToken(payload.content ?? '')
        else if (payload.type === 'done') callbacks.onDone()
        else if (payload.type === 'error') callbacks.onError(payload.message ?? 'Error')
      } catch {
        // skip malformed lines
      }
    }
  }
}
