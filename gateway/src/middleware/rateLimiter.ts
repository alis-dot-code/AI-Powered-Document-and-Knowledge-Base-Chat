import rateLimit from 'express-rate-limit'
import { RedisStore } from 'rate-limit-redis'
import { redis } from '@/config/redis'
import { env } from '@/config/env'

export const rateLimiter = rateLimit({
  windowMs: env.RATE_LIMIT_WINDOW_MS,
  max: env.RATE_LIMIT_MAX_REQUESTS,
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => {
    // Rate-limit by user ID if authenticated, else by IP
    const authReq = req as { user?: { sub?: string } }
    return authReq.user?.sub ?? req.ip ?? 'unknown'
  },
  store: new RedisStore({
    sendCommand: (...args: string[]) => redis.call(...args) as Promise<number>,
  }),
  handler: (_req, res) => {
    res.status(429).json({
      error: { code: 'RATE_LIMITED', message: 'Too many requests. Please slow down.' },
    })
  },
})

/** Stricter limiter for auth endpoints */
export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  store: new RedisStore({
    sendCommand: (...args: string[]) => redis.call(...args) as Promise<number>,
    prefix: 'rl:auth:',
  }),
  handler: (_req, res) => {
    res.status(429).json({
      error: { code: 'RATE_LIMITED', message: 'Too many auth attempts. Try again later.' },
    })
  },
})
