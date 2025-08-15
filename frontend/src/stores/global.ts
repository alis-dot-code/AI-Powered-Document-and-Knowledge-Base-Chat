import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Workspace } from '@/types'

interface GlobalState {
  activeWorkspaceId: string | null
  setActiveWorkspaceId: (id: string | null) => void
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

export const useGlobalStore = create<GlobalState>()(
  persist(
    (set) => ({
      activeWorkspaceId: null,
      setActiveWorkspaceId: (id) => set({ activeWorkspaceId: id }),
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: 'docmind-global',
      partialize: (state) => ({ activeWorkspaceId: state.activeWorkspaceId }),
    }
  )
)
