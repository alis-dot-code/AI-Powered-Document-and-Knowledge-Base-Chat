import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
  'text/csv': ['.csv'],
}

interface UploadDropzoneProps {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

export function UploadDropzone({ onFiles, disabled }: UploadDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length) onFiles(accepted)
    },
    [onFiles]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: 50 * 1024 * 1024,
    disabled,
    multiple: true,
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 text-center transition-colors cursor-pointer',
        isDragActive
          ? 'border-primary-400 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50',
        disabled && 'cursor-not-allowed opacity-50'
      )}
    >
      <input {...getInputProps()} />
      <UploadCloud
        className={cn('h-10 w-10', isDragActive ? 'text-primary-500' : 'text-gray-400')}
      />
      <div>
        <p className="text-sm font-medium text-gray-700">
          {isDragActive ? 'Drop files here' : 'Drag & drop files, or click to browse'}
        </p>
        <p className="mt-1 text-xs text-gray-500">
          PDF, DOCX, TXT, CSV — up to 50 MB each
        </p>
      </div>
    </div>
  )
}
