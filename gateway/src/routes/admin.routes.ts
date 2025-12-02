import { Router } from 'express'
import { authenticate } from '@/middleware/authenticate'
import { fastapiProxy } from '@/proxy/fastapi.proxy'

const router = Router()

// All admin routes require authentication — superadmin check is in FastAPI
router.use(authenticate)

router.get('/stats', fastapiProxy)
router.get('/users', fastapiProxy)
router.patch('/users/:userId', fastapiProxy)
router.get('/workspaces', fastapiProxy)

export default router
