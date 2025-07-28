import { NextFunction, Request, Response } from 'express'
import { extractTokenFromRequest, verifyAccessToken } from '@/services/jwt.service'
import { AuthenticatedRequest } from '@/types'
import { UnauthorizedError } from '@/utils/errors'

export function authenticate(req: Request, res: Response, next: NextFunction): void {
  const token = extractTokenFromRequest(
    req.cookies ?? {},
    req.headers.authorization,
  )
  if (!token) {
    return next(new UnauthorizedError('Authentication token not provided'))
  }
  try {
    const payload = verifyAccessToken(token)
    ;(req as AuthenticatedRequest).user = payload
    next()
  } catch (err) {
    next(err)
  }
}

/** Same as authenticate but doesn't block — attaches user if token present. */
export function optionalAuthenticate(req: Request, _res: Response, next: NextFunction): void {
  const token = extractTokenFromRequest(req.cookies ?? {}, req.headers.authorization)
  if (token) {
    try {
      ;(req as AuthenticatedRequest).user = verifyAccessToken(token)
    } catch {
      // silently ignore invalid token for optional auth
    }
  }
  next()
}
