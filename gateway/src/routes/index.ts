import { Router } from 'express'
import authRoutes from './auth.routes'
import workspaceRoutes from './workspace.routes'
import documentRoutes from './document.routes'
import chatRoutes from './chat.routes'
// Future routers — uncomment as each prompt is implemented:
import billingRoutes from './billing.routes'
import widgetRoutes from './widget.routes'
import adminRoutes from './admin.routes'

const router = Router()

router.use('/api/v1/auth', authRoutes)
router.use('/api/v1/workspaces', workspaceRoutes)
router.use('/api/v1/workspaces/:workspaceId/documents', documentRoutes)
router.use('/api/v1/workspaces/:workspaceId/chat', chatRoutes)
router.use('/api/v1/billing', billingRoutes)
router.use('/api/v1/widget', widgetRoutes)
router.use('/api/v1/admin', adminRoutes)

export default router
