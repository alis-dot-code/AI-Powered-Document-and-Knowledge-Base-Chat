import { Router } from 'express'
import { apiKeyAuth, widgetCors } from '@/middleware/apiKeyAuth'
import { fastapiProxy } from '@/proxy/fastapi.proxy'
import { sseProxy } from '@/proxy/sse.proxy'

const router = Router()

// Widget routes use open CORS (embeddable anywhere) + API key auth
router.use(widgetCors)
router.use(apiKeyAuth)

// Widget config
router.get('/config', fastapiProxy)

// Session management
router.post('/sessions', fastapiProxy)

// SSE chat stream
router.post('/sessions/:sessionId/chat', sseProxy)

export default router
