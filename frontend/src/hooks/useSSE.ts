import { useCallback, useRef, useState } from 'react'
import { fetchSSE } from '@/lib/sse'
import type { SSECitation } from '@/features/chat/types'

export interface UseSSEResult {
  streaming: boolean
  streamingText: string
  send: (url: string, body: unknown) => Promise<void>
  cancel: () => void
}

export function useSSE(options: {
  onToken?: (token: string) => void
  onCitations?: (citations: SSECitation[]) => void
  onDone?: (text: string, citations: SSECitation[]) => void
  onError?: (message: string) => void
}): UseSSEResult {
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const abortRef = useRef<AbortController | null>(null)
  const accRef = useRef('')
  const citationsRef = useRef<SSECitation[]>([])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const send = useCallback(
    async (url: string, body: unknown) => {
      // Cancel any in-flight stream
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      accRef.current = ''
      citationsRef.current = []
      setStreamingText('')
      setStreaming(true)

      try {
        await fetchSSE({
          url,
          body,
          signal: controller.signal,
          onToken: (token) => {
            accRef.current += token
            setStreamingText(accRef.current)
            options.onToken?.(token)
          },
          onCitations: (raw) => {
            citationsRef.current = raw as SSECitation[]
            options.onCitations?.(raw as SSECitation[])
          },
          onDone: () => {
            options.onDone?.(accRef.current, citationsRef.current)
            setStreaming(false)
            setStreamingText('')
          },
          onError: (msg) => {
            options.onError?.(msg)
            setStreaming(false)
            setStreamingText('')
          },
        })
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') {
          options.onError?.(err.message)
        }
        setStreaming(false)
        setStreamingText('')
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  return { streaming, streamingText, send, cancel }
}
