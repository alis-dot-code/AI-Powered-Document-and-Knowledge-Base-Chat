import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { attachWorkspaceContext } from '@/middleware/workspaceAccess'
import { fastapiProxy } from '@/proxy/fastapi.proxy'

const router = Router({ mergeParams: true })

// Workspace-scoped — mounted at /api/v1/workspaces/:workspaceId/documents
router.use(authenticate)
router.use(attachWorkspaceContext)

router.post('/', fastapiProxy)           // upload (multipart)
router.post('/scrape', fastapiProxy)     // url scrape
router.get('/', fastapiProxy)            // list
router.get('/:documentId', fastapiProxy)
router.get('/:documentId/status', fastapiProxy)
router.patch('/:documentId', fastapiProxy)
router.delete('/:documentId', fastapiProxy)
router.post('/:documentId/reprocess', fastapiProxy)

export default router
