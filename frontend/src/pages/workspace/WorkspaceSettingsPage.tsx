import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { UserPlus, Trash2 } from 'lucide-react'
import { useWorkspace, useUpdateWorkspace, useDeleteWorkspace } from '@/features/workspace/hooks'
import { useAuthStore } from '@/features/auth/store'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { MemberList } from '@/components/workspace/MemberList'
import { InviteModal } from '@/components/workspace/InviteModal'

const schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
})

type FormValues = z.infer<typeof schema>

export function WorkspaceSettingsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const user = useAuthStore((s) => s.user)
  const { data: ws, isLoading } = useWorkspace(workspaceId!)
  const update = useUpdateWorkspace(workspaceId!)
  const deleteWs = useDeleteWorkspace()
  const navigate = useNavigate()
  const [inviteOpen, setInviteOpen] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: { name: ws?.name ?? '', description: ws?.description ?? '' },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    )
  }

  if (!ws) {
    return (
      <div className="p-8 text-gray-500">Workspace not found.</div>
    )
  }

  const canEdit = ws.current_user_role === 'owner' || ws.current_user_role === 'admin'
  const isOwner = ws.current_user_role === 'owner'

  return (
    <div className="mx-auto max-w-2xl p-8 flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">{ws.name}</h1>
        <p className="text-sm text-gray-500">/{ws.slug}</p>
      </div>

      {/* General settings */}
      {canEdit && (
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-gray-900">General</h2>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleSubmit((d) => update.mutate(d))}
              className="flex flex-col gap-4"
            >
              <Input
                label="Name"
                error={errors.name?.message}
                {...register('name')}
              />
              <Input
                label="Description"
                error={errors.description?.message}
                {...register('description')}
              />
              <div className="flex justify-end">
                <Button type="submit" loading={update.isPending} size="sm">
                  Save changes
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Members */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900">
              Members ({ws.member_count})
            </h2>
            {canEdit && (
              <Button size="sm" onClick={() => setInviteOpen(true)}>
                <UserPlus className="h-4 w-4" />
                Invite
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <MemberList
            workspaceId={workspaceId!}
            members={ws.members}
            currentUserRole={ws.current_user_role}
            currentUserId={user?.id ?? ''}
          />
        </CardContent>
      </Card>

      {/* Danger zone */}
      {isOwner && (
        <Card className="border-red-200">
          <CardHeader>
            <h2 className="text-sm font-semibold text-red-700">Danger zone</h2>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Delete workspace</p>
              <p className="text-xs text-gray-500">
                This is permanent and cannot be undone.
              </p>
            </div>
            <Button
              variant="danger"
              size="sm"
              loading={deleteWs.isPending}
              onClick={() => {
                if (confirm('Delete this workspace? This cannot be undone.')) {
                  deleteWs.mutate(workspaceId!)
                }
              }}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </CardContent>
        </Card>
      )}

      <InviteModal
        workspaceId={workspaceId!}
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
      />
    </div>
  )
}
