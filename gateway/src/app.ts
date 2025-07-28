import express from 'express'
import cookieParser from 'cookie-parser'
import helmet from 'helmet'
import { corsMiddleware } from '@/config/cors'
import { requestLogger } from '@/middleware/requestLogger'
import { rateLimiter } from '@/middleware/rateLimiter'
import { errorHandler } from '@/middleware/errorHandler'
import routes from '@/routes/index'

const app = express()

// ---------------------------------------------------------------------------
// Security & parsing
// ---------------------------------------------------------------------------
app.set('trust proxy', 1)
app.use(helmet({ contentSecurityPolicy: false }))
app.use(corsMiddleware)
app.use(cookieParser())
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------
app.use(requestLogger)

// ---------------------------------------------------------------------------
// Global rate limiter (per-route limiters applied in route files)
// ---------------------------------------------------------------------------
app.use(rateLimiter)

// ---------------------------------------------------------------------------
// Health check — bypass auth and rate limiting
// ---------------------------------------------------------------------------
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'gateway' })
})

// ---------------------------------------------------------------------------
// API routes
// ---------------------------------------------------------------------------
app.use(routes)

// ---------------------------------------------------------------------------
// 404 handler
// ---------------------------------------------------------------------------
app.use((_req, res) => {
  res.status(404).json({ error: { code: 'NOT_FOUND', message: 'Route not found' } })
})

// ---------------------------------------------------------------------------
// Global error handler (must be last)
// ---------------------------------------------------------------------------
app.use(errorHandler)

export default app
