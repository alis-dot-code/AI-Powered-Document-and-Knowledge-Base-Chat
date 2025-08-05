import { NextFunction, Request, Response } from 'express'
import { AuthenticatedRequest, Role, WorkspaceAccessRequest } from '@/types'
import { ForbiddenError, NotFoundError, UnauthorizedError } from '@/utils/errors'

const ROLE_HIERARCHY: Record<Role, number> = {
  viewer: 1,
  editor: 2,
  admin: 3,
  owner: 4,
}

export function requireRole(minimumRole: Role) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const authReq = req as WorkspaceAccessRequest
    if (!authReq.user) return next(new UnauthorizedError())

    const userRole = authReq.userRole
    if (!userRole) return next(new ForbiddenError('No role in this workspace'))

    if (ROLE_HIERARCHY[userRole] < ROLE_HIERARCHY[minimumRole]) {
      return next(
        new ForbiddenError(`This action requires the '${minimumRole}' role or higher`),
      )
    }
    next()
  }
}

/**
 * Attaches workspaceId to request and injects x-user-id / x-workspace-id headers
 * so FastAPI can enforce membership + role without re-verifying the JWT.
 * Must run after `authenticate`.
 */
export function attachWorkspaceContext(req: Request, _res: Response, next: NextFunction): void {
  const authReq = req as WorkspaceAccessRequest
  if (!authReq.user) return next(new UnauthorizedError())

  const workspaceId = req.params['workspaceId']
  if (!workspaceId) return next(new NotFoundError('Workspace'))

  authReq.workspaceId = workspaceId
  req.headers['x-user-id'] = authReq.user.sub
  req.headers['x-workspace-id'] = workspaceId
  next()
}
