import { useNavigate } from 'react-router-dom'
import { Plus, FileText, MessageSquare, Users } from 'lucide-react'
import { useAuthStore } from '@/features/auth/store'
import { useWorkspaces } from '@/features/workspace/hooks'
import { useGlobalStore } from '@/stores/global'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { formatDate, getInitials } from '@/lib/utils'

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { data: workspaces, isLoading } = useWorkspaces()
  const { setActiveWorkspaceId } = useGlobalStore()
  const navigate = useNavigate()

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {greeting()}, {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Here's an overview of your workspaces.
        </p>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Your workspaces</h2>
        <Button
          size="sm"
          onClick={() => navigate('/workspaces/new')}
          className="gap-1.5"
        >
          <Plus className="h-4 w-4" />
          New workspace
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : workspaces?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
              <FileText className="h-6 w-6 text-gray-400" />
            </div>
            <div>
              <p className="font-medium text-gray-900">No workspaces yet</p>
              <p className="mt-1 text-sm text-gray-500">
                Create your first workspace to get started.
              </p>
            </div>
            <Button onClick={() => navigate('/workspaces/new')}>
              Create workspace
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces?.map((ws) => (
            <Card
              key={ws.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => {
                setActiveWorkspaceId(ws.id)
                navigate(`/workspaces/${ws.id}`)
              }}
            >
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">
                    {getInitials(ws.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-gray-900">{ws.name}</p>
                    <p className="truncate text-xs text-gray-500">/{ws.slug}</p>
                  </div>
                </div>
                {ws.description && (
                  <p className="line-clamp-2 text-sm text-gray-600">{ws.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" />
                    {ws.member_count} member{ws.member_count !== 1 ? 's' : ''}
                  </span>
                  <span>Created {formatDate(ws.created_at)}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
