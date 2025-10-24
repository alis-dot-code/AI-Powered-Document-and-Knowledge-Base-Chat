import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { fastapiProxy } from '@/proxy/fastapi.proxy'

const router = Router({ mergeParams: true })

// Public — Stripe webhook must bypass auth (signature verified by FastAPI)
router.post('/webhook/stripe', fastapiProxy)

// Public — plan listing
router.get('/plans', fastapiProxy)

// Authenticated routes
router.use(authenticate)

// Workspace-scoped billing
router.get('/workspaces/:workspaceId/subscription', fastapiProxy)
router.post('/workspaces/:workspaceId/checkout', fastapiProxy)
router.post('/workspaces/:workspaceId/portal', fastapiProxy)
router.get('/workspaces/:workspaceId/usage', fastapiProxy)

export default router
