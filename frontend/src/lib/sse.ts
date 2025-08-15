/**
 * Minimal SSE client using the Fetch API with ReadableStream.
 * Unlike EventSource, this supports POST requests with a body.
 */
export interface SSEOptions {
  url: string
  body: unknown
  onToken: (token: string) => void
  onCitations: (citations: unknown[]) => void
  onDone: () => void
  onError: (message: string) => void
  signal?: AbortSignal
}

export async function fetchSSE({
  url,
  body,
  onToken,
  onCitations,
  onDone,
  onError,
  signal,
}: SSEOptions): Promise<void> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    credentials: 'include',
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    onError(`HTTP ${response.status}`)
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('No response body')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE lines end with \n\n
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          let event: Record<string, unknown>
          try {
            event = JSON.parse(raw)
          } catch {
            continue
          }

          switch (event.type) {
            case 'token':
              onToken(event.content as string)
              break
            case 'citations':
              onCitations(event.citations as unknown[])
              break
            case 'done':
              onDone()
              break
            case 'error':
              onError(event.message as string)
              break
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
