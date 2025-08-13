import { MoreHorizontal } from 'lucide-react'
import type { WorkspaceMember, WorkspaceRole } from '@/types'
import { Badge } from '@/components/ui/Badge'
import { Dropdown } from '@/components/ui/Dropdown'
import { getInitials } from '@/lib/utils'
import { useUpdateMemberRole, useRemoveMember } from '@/features/workspace/hooks'

const roleBadgeVariant: Record<WorkspaceRole, 'info' | 'warning' | 'default' | 'success'> = {
  owner: 'info',
  admin: 'warning',
  member: 'default',
  viewer: 'default',
}

interface MemberListProps {
  workspaceId: string
  members: WorkspaceMember[]
  currentUserRole: WorkspaceRole
  currentUserId: string
}

export function MemberList({
  workspaceId,
  members,
  currentUserRole,
  currentUserId,
}: MemberListProps) {
  const updateRole = useUpdateMemberRole(workspaceId)
  const removeMember = useRemoveMember(workspaceId)

  const canManage = currentUserRole === 'owner' || currentUserRole === 'admin'

  return (
    <ul className="divide-y divide-gray-100">
      {members.map((m) => (
        <li key={m.id} className="flex items-center gap-4 py-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-200 text-sm font-semibold text-gray-600">
            {m.full_name ? getInitials(m.full_name) : m.email[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-gray-900">
              {m.full_name ?? m.email}
            </p>
            {m.full_name && (
              <p className="truncate text-xs text-gray-500">{m.email}</p>
            )}
          </div>
          <Badge variant={roleBadgeVariant[m.role]}>{m.role}</Badge>
          {m.invite_status === 'pending' && (
            <Badge variant="warning">pending</Badge>
          )}
          {canManage && m.role !== 'owner' && m.user_id !== currentUserId && (
            <Dropdown
              trigger={
                <button className="rounded p-1 hover:bg-gray-100">
                  <MoreHorizontal className="h-4 w-4 text-gray-500" />
                </button>
              }
              items={[
                {
                  label: 'Make admin',
                  onClick: () =>
                    m.user_id &&
                    updateRole.mutate({ userId: m.user_id, data: { role: 'admin' } }),
                },
                {
                  label: 'Make member',
                  onClick: () =>
                    m.user_id &&
                    updateRole.mutate({ userId: m.user_id, data: { role: 'member' } }),
                },
                {
                  label: 'Make viewer',
                  onClick: () =>
                    m.user_id &&
                    updateRole.mutate({ userId: m.user_id, data: { role: 'viewer' } }),
                },
                {
                  label: 'Remove',
                  danger: true,
                  onClick: () =>
                    m.user_id && removeMember.mutate(m.user_id),
                },
              ]}
            />
          )}
        </li>
      ))}
    </ul>
  )
}
