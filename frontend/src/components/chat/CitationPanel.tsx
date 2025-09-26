import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react'
import { useDocuments } from '@/features/documents/hooks'
import { useGlobalStore } from '@/stores/global'
import type { Citation } from '@/features/chat/types'
import { cn } from '@/lib/utils'

interface CitationPanelProps {
  citations: Citation[]
}

export function CitationPanel({ citations }: CitationPanelProps) {
  const { activeWorkspaceId } = useGlobalStore()
  const { data: documents } = useDocuments(activeWorkspaceId ?? '')
  const [expanded, setExpanded] = useState<string | null>(null)

  if (!citations.length) return null

  const docMap = new Map(documents?.map((d) => [d.id, d]) ?? [])

  return (
    <div className="mt-3 rounded-xl border border-gray-200 bg-gray-50 text-xs">
      <button
        onClick={() => setExpanded(expanded === 'panel' ? null : 'panel')}
        className="flex w-full items-center justify-between px-3 py-2 text-gray-500 hover:text-gray-700"
      >
        <span className="font-medium">
          {citations.length} source{citations.length !== 1 ? 's' : ''}
        </span>
        {expanded === 'panel' ? (
          <ChevronUp className="h-3.5 w-3.5" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" />
        )}
      </button>

      {expanded === 'panel' && (
        <div className="divide-y divide-gray-200 border-t border-gray-200">
          {citations.map((c) => {
            const doc = docMap.get(c.document_id)
            const isOpen = expanded === c.id

            return (
              <div key={c.id} className="px-3 py-2">
                {/* Header row */}
                <button
                  onClick={() => setExpanded(isOpen ? 'panel' : c.id)}
                  className="flex w-full items-start gap-2 text-left"
                >
                  <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gray-400" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium text-gray-700">
                      {doc?.title ?? `Document ${c.document_id.slice(0, 8)}`}
                    </p>
                    <div className="mt-0.5 flex items-center gap-2 text-gray-400">
                      {c.page_number != null && <span>Page {c.page_number}</span>}
                      {c.score != null && (
                        <span
                          className={cn(
                            'rounded px-1 py-0.5 font-medium',
                            c.score >= 0.85
                              ? 'bg-green-100 text-green-700'
                              : c.score >= 0.7
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-500'
                          )}
                        >
                          {(c.score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                  </div>
                  {isOpen ? (
                    <ChevronUp className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                  )}
                </button>

                {/* Excerpt */}
                {isOpen && (
                  <div className="mt-2 rounded-lg border border-gray-200 bg-white p-2 text-gray-600 leading-relaxed">
                    <p className="line-clamp-6 whitespace-pre-wrap">{c.content_snapshot}</p>
                    {doc?.source_url && (
                      <a
                        href={doc.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1.5 inline-flex items-center gap-1 text-primary-600 hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" />
                        View source
                      </a>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
