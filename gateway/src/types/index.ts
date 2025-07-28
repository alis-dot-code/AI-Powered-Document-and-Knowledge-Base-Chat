import { Request } from 'express'

export interface JwtPayload {
  sub: string        // user UUID
  type: 'access' | 'refresh'
  iat: number
  exp: number
  jti: string
}

export interface AuthenticatedRequest extends Request {
  user: JwtPayload
}

export interface ApiKeyPayload {
  id: string
  workspaceId: string
  keyPrefix: string
}

export interface ApiKeyRequest extends Request {
  apiKey: ApiKeyPayload
}

export type Role = 'owner' | 'admin' | 'editor' | 'viewer'

export interface WorkspaceAccessRequest extends AuthenticatedRequest {
  workspaceId: string
  userRole: Role
}
