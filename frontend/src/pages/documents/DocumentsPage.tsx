import { useState } from 'react'
import { Link as LinkIcon, Upload } from 'lucide-react'
import { useGlobalStore } from '@/stores/global'
import {
  useDocuments,
  useUploadDocument,
  useDeleteDocument,
  useReprocessDocument,
} from '@/features/documents/hooks'
import { UploadDropzone } from '@/components/documents/UploadDropzone'
import { DocumentCard } from '@/components/documents/DocumentCard'
import { UrlScrapeForm } from '@/components/documents/UrlScrapeForm'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'

export function DocumentsPage() {
  const { activeWorkspaceId } = useGlobalStore()
  const [scrapeOpen, setScrapeOpen] = useState(false)

  const { data: docs, isLoading } = useDocuments(activeWorkspaceId ?? '')
  const upload = useUploadDocument(activeWorkspaceId ?? '')
  const deleteDoc = useDeleteDocument(activeWorkspaceId ?? '')
  const reprocess = useReprocessDocument(activeWorkspaceId ?? '')

  if (!activeWorkspaceId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        Select a workspace to view documents.
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Documents</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload files or scrape URLs to build your knowledge base.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setScrapeOpen(true)}
        >
          <LinkIcon className="h-4 w-4" />
          Scrape URL
        </Button>
      </div>

      <UploadDropzone
        disabled={upload.isPending}
        onFiles={(files) => files.forEach((f) => upload.mutate(f))}
      />

      <div className="mt-8">
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner />
          </div>
        ) : !docs?.length ? (
          <div className="py-10 text-center text-sm text-gray-400">
            No documents yet. Upload a file or scrape a URL above.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {docs.map((doc) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onDelete={(id) => {
                  if (confirm('Delete this document?')) deleteDoc.mutate(id)
                }}
                onReprocess={(id) => reprocess.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        open={scrapeOpen}
        onClose={() => setScrapeOpen(false)}
        title="Scrape URL"
      >
        <UrlScrapeForm
          workspaceId={activeWorkspaceId}
          onSuccess={() => setScrapeOpen(false)}
        />
      </Modal>
    </div>
  )
}
