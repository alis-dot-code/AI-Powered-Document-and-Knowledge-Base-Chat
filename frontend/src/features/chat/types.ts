export interface ChatSession {
  id: string
  workspace_id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Citation {
  id: string
  chunk_id: string
  document_id: string
  content_snapshot: string
  page_number: number | null
  score: number | null
}

export interface ChatMessage {
  id: string
  session_id: string
  workspace_id: string
  role: 'user' | 'assistant'
  content: string
  token_count: number
  created_at: string
  citations: Citation[]
}

export interface ChatHistoryResponse {
  session: ChatSession
  messages: ChatMessage[]
}

// SSE event payloads
export type SSEEvent =
  | { type: 'token'; content: string }
  | { type: 'citations'; citations: SSECitation[] }
  | { type: 'done' }
  | { type: 'error'; message: string }

export interface SSECitation {
  chunk_id: string
  document_id: string
  content: string
  page_number: number | null
  score: number
}
