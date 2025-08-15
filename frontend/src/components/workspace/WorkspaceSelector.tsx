import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, Plus, Check } from 'lucide-react'
import { useWorkspaces } from '@/features/workspace/hooks'
import { useGlobalStore } from '@/stores/global'
import { useClickOutside } from '@/hooks/useClickOutside'
import { getInitials, cn } from '@/lib/utils'
import { Spinner } from '@/components/ui/Spinner'

export function WorkspaceSelector() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { data: workspaces, isLoading } = useWorkspaces()
  const { activeWorkspaceId, setActiveWorkspaceId } = useGlobalStore()

  useClickOutside(ref, () => setOpen(false))

  const active = workspaces?.find((w) => w.id === activeWorkspaceId) ?? workspaces?.[0]

  if (isLoading) return <Spinner size="sm" />

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 w-full"
      >
        {active ? (
          <>
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary-600 text-xs font-bold text-white shrink-0">
              {getInitials(active.name)}
            </span>
            <span className="flex-1 truncate text-left">{active.name}</span>
          </>
        ) : (
          <span className="flex-1 text-gray-400">Select workspace</span>
        )}
        <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          {workspaces?.map((ws) => (
            <button
              key={ws.id}
              onClick={() => {
                setActiveWorkspaceId(ws.id)
                setOpen(false)
                navigate(`/workspaces/${ws.id}`)
              }}
              className="flex w-full items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary-600 text-xs font-bold text-white shrink-0">
                {getInitials(ws.name)}
              </span>
              <span className="flex-1 truncate text-left">{ws.name}</span>
              {ws.id === active?.id && (
                <Check className="h-4 w-4 text-primary-600 shrink-0" />
              )}
            </button>
          ))}

          <div className="my-1 border-t border-gray-100" />

          <button
            onClick={() => {
              setOpen(false)
              navigate('/workspaces/new')
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <Plus className="h-4 w-4" />
            New workspace
          </button>
        </div>
      )}
    </div>
  )
}
