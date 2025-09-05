import { FileText, Trash2, RefreshCw, MoreHorizontal } from 'lucide-react'
import type { Document } from '@/features/documents/types'
import { ProcessingStatus } from './ProcessingStatus'
import { Dropdown } from '@/components/ui/Dropdown'
import { formatDate } from '@/lib/utils'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

interface DocumentCardProps {
  doc: Document
  onDelete: (id: string) => void
  onReprocess: (id: string) => void
}

export function DocumentCard({ doc, onDelete, onReprocess }: DocumentCardProps) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100">
        <FileText className="h-5 w-5 text-gray-500" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium text-gray-900">{doc.title}</p>
        <div className="mt-0.5 flex items-center gap-3 text-xs text-gray-500">
          <span>{formatBytes(doc.file_size)}</span>
          {doc.status === 'completed' && (
            <span>{doc.chunk_count} chunks</span>
          )}
          <span>{formatDate(doc.created_at)}</span>
        </div>
      </div>

      <ProcessingStatus status={doc.status} />

      <Dropdown
        trigger={
          <button className="rounded p-1 hover:bg-gray-100">
            <MoreHorizontal className="h-4 w-4 text-gray-500" />
          </button>
        }
        items={[
          {
            label: 'Reprocess',
            icon: <RefreshCw className="h-4 w-4" />,
            onClick: () => onReprocess(doc.id),
          },
          {
            label: 'Delete',
            danger: true,
            icon: <Trash2 className="h-4 w-4" />,
            onClick: () => onDelete(doc.id),
          },
        ]}
      />
    </div>
  )
}
