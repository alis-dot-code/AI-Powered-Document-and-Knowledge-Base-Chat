import { CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react'
import type { DocumentStatus } from '@/features/documents/types'
import { cn } from '@/lib/utils'

interface ProcessingStatusProps {
  status: DocumentStatus
  className?: string
}

const config: Record<
  DocumentStatus,
  { icon: React.ElementType; label: string; color: string; spin?: boolean }
> = {
  pending: { icon: Clock, label: 'Pending', color: 'text-gray-400' },
  processing: { icon: Loader2, label: 'Processing', color: 'text-blue-500', spin: true },
  completed: { icon: CheckCircle, label: 'Ready', color: 'text-green-500' },
  failed: { icon: XCircle, label: 'Failed', color: 'text-red-500' },
}

export function ProcessingStatus({ status, className }: ProcessingStatusProps) {
  const { icon: Icon, label, color, spin } = config[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-xs font-medium', color, className)}>
      <Icon className={cn('h-3.5 w-3.5', spin && 'animate-spin')} />
      {label}
    </span>
  )
}
