// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface User {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  is_active: boolean
  is_superadmin: boolean
  email_verified: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ---------------------------------------------------------------------------
// Workspace
// ---------------------------------------------------------------------------

export type WorkspaceRole = 'owner' | 'admin' | 'member' | 'viewer'
export type InviteStatus = 'pending' | 'accepted'

export interface Workspace {
  id: string
  owner_id: string
  name: string
  slug: string
  description: string | null
  logo_url: string | null
  member_count: number
  created_at: string
  updated_at: string
}

export interface WorkspaceMember {
  id: string
  user_id: string | null
  email: string
  full_name: string | null
  avatar_url: string | null
  role: WorkspaceRole
  invite_status: InviteStatus
  created_at: string
}

export interface WorkspaceDetail extends Workspace {
  members: WorkspaceMember[]
  current_user_role: WorkspaceRole
}

// ---------------------------------------------------------------------------
// API error shape
// ---------------------------------------------------------------------------

export interface ApiError {
  error: {
    code: string
    message: string
    details?: unknown
  }
}
