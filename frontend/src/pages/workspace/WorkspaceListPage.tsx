import { useNavigate } from 'react-router-dom'
import { Plus, Users } from 'lucide-react'
import { useWorkspaces } from '@/features/workspace/hooks'
import { useGlobalStore } from '@/stores/global'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { formatDate, getInitials } from '@/lib/utils'

export function WorkspaceListPage() {
  const { data: workspaces, isLoading } = useWorkspaces()
  const { setActiveWorkspaceId } = useGlobalStore()
  const navigate = useNavigate()

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Workspaces</h1>
        <Button size="sm" onClick={() => navigate('/workspaces/new')}>
          <Plus className="h-4 w-4" />
          New
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {workspaces?.map((ws) => (
            <Card
              key={ws.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => {
                setActiveWorkspaceId(ws.id)
                navigate(`/workspaces/${ws.id}`)
              }}
            >
              <CardContent className="flex items-center gap-4 py-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">
                  {getInitials(ws.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900">{ws.name}</p>
                  <p className="text-xs text-gray-500">/{ws.slug}</p>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Users className="h-3.5 w-3.5" />
                  {ws.member_count}
                </div>
                <span className="text-xs text-gray-400">{formatDate(ws.created_at)}</span>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
