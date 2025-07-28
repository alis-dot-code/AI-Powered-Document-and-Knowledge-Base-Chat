import jwt from 'jsonwebtoken'
import { env } from '@/config/env'
import { JwtPayload } from '@/types'
import { UnauthorizedError } from '@/utils/errors'

export function verifyAccessToken(token: string): JwtPayload {
  try {
    const payload = jwt.verify(token, env.JWT_SECRET_KEY) as JwtPayload
    if (payload.type !== 'access') {
      throw new UnauthorizedError('Invalid token type')
    }
    return payload
  } catch (err) {
    if (err instanceof UnauthorizedError) throw err
    throw new UnauthorizedError('Invalid or expired token')
  }
}

export function extractTokenFromRequest(
  cookies: Record<string, string>,
  authHeader: string | undefined,
): string | null {
  if (cookies['access_token']) return cookies['access_token']
  if (authHeader?.startsWith('Bearer ')) return authHeader.slice(7).trim()
  return null
}
