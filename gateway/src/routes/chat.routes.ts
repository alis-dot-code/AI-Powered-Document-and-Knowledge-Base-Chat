import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { attachWorkspaceContext } from '@/middleware/workspaceAccess'
import { fastapiProxy } from '@/proxy/fastapi.proxy'
import { sseProxy } from '@/proxy/sse.proxy'

const router = Router({ mergeParams: true })

// Workspace-scoped — mounted at /api/v1/workspaces/:workspaceId/chat
router.use(authenticate)
router.use(attachWorkspaceContext)

// Session CRUD — standard JSON proxy
router.post('/sessions', fastapiProxy)
router.get('/sessions', fastapiProxy)
router.get('/sessions/:sessionId', fastapiProxy)
router.patch('/sessions/:sessionId', fastapiProxy)
router.delete('/sessions/:sessionId', fastapiProxy)

// Message history + citations — standard JSON proxy
router.get('/sessions/:sessionId/messages', fastapiProxy)
router.get('/sessions/:sessionId/messages/:messageId/citations', fastapiProxy)

// SSE streaming message endpoint — must use sseProxy (no compression, no buffering)
router.post('/sessions/:sessionId/messages', sseProxy)

export default router
