import { NextFunction, Request, Response } from 'express'
import { UnauthorizedError } from '@/utils/errors'

/**
 * Validates the Bearer API key from the Authorization header.
 * The key itself is verified by FastAPI (bcrypt). The gateway only:
 *  1. Checks the header is present and well-formed.
 *  2. Forwards the raw key to FastAPI via the Authorization header.
 *  3. Enforces open CORS for embeddable widget (origin restriction per key is in FastAPI).
 *
 * FastAPI performs the actual key lookup + hash verification.
 */
export function apiKeyAuth(req: Request, res: Response, next: NextFunction): void {
  const auth = req.headers.authorization
  if (!auth || !auth.startsWith('Bearer ')) {
    return next(new UnauthorizedError('API key required'))
  }

  const raw = auth.slice(7).trim()
  if (!raw.startsWith('dm_')) {
    return next(new UnauthorizedError('Invalid API key format'))
  }

  // Pass key through to FastAPI — it will verify the hash and resolve workspace
  next()
}

/**
 * Widget-specific CORS: allows any origin (widget is embeddable anywhere).
 * Origin restriction per API key is enforced by FastAPI via allowed_origins field.
 */
export function widgetCors(req: Request, res: Response, next: NextFunction): void {
  const origin = req.headers.origin
  if (origin) {
    res.setHeader('Access-Control-Allow-Origin', origin)
    res.setHeader('Vary', 'Origin')
  } else {
    res.setHeader('Access-Control-Allow-Origin', '*')
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.sendStatus(204)
    return
  }
  next()
}
