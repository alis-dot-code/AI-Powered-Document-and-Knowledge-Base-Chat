import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { fastapiProxy } from '@/proxy/fastapi.proxy'

const router = Router()

// All workspace routes require authentication
router.use(authenticate)

// Workspace CRUD
router.post('/', fastapiProxy)
router.get('/', fastapiProxy)
router.get('/:workspaceId', fastapiProxy)
router.patch('/:workspaceId', fastapiProxy)
router.delete('/:workspaceId', fastapiProxy)

// Member management
router.post('/:workspaceId/invite', fastapiProxy)
router.post('/accept-invite/:inviteToken', fastapiProxy)
router.get('/:workspaceId/members', fastapiProxy)
router.patch('/:workspaceId/members/:userId', fastapiProxy)
router.delete('/:workspaceId/members/:userId', fastapiProxy)

export default router
