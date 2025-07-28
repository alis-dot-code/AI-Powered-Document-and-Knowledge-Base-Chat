import { Router } from 'express'
import { authRateLimiter } from '@/middleware/rateLimiter'
import { authenticate } from '@/middleware/authenticate'
import { fastapiProxy } from '@/proxy/fastapi.proxy'

const router = Router()

// Auth routes — proxy directly to FastAPI.
// Rate-limit login/register to prevent brute force.
router.post('/register', authRateLimiter, fastapiProxy)
router.post('/login', authRateLimiter, fastapiProxy)
router.post('/logout', fastapiProxy)
router.post('/refresh', fastapiProxy)
router.post('/forgot-password', authRateLimiter, fastapiProxy)
router.post('/reset-password', fastapiProxy)
router.post('/verify-email', fastapiProxy)

// Protected auth routes — validate JWT at gateway before forwarding
router.get('/me', authenticate, fastapiProxy)
router.patch('/me', authenticate, fastapiProxy)

export default router
