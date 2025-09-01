export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type DocumentSource = 'upload' | 'url_scrape'

export interface Document {
  id: string
  workspace_id: string
  uploaded_by: string | null
  title: string
  filename: string
  mime_type: string
  file_size: number
  source: DocumentSource
  source_url: string | null
  status: DocumentStatus
  error_message: string | null
  chunk_count: number
  page_count: number | null
  created_at: string
  updated_at: string
}

export interface DocumentStatusResponse {
  id: string
  status: DocumentStatus
  chunk_count: number
  error_message: string | null
}

export interface ScrapeUrlRequest {
  url: string
  title?: string
}
