import { NextFunction, Request, Response } from 'express'
import { AppError } from '@/utils/errors'
import { logger } from '@/utils/logger'

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction,
): void {
  if (err instanceof AppError) {
    res.status(err.statusCode).json({
      error: { code: err.code, message: err.message },
    })
    return
  }

  // CORS errors from the cors package come through as plain Errors
  if (err.message?.startsWith('CORS:')) {
    res.status(403).json({ error: { code: 'CORS_BLOCKED', message: err.message } })
    return
  }

  logger.error({ err, method: req.method, url: req.url }, 'Unhandled gateway error')
  res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
  })
}
