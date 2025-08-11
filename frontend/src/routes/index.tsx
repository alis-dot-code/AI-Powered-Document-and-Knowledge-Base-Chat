import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AuthLayout } from '@/layouts/AuthLayout'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { PublicRoute } from './PublicRoute'

// Auth pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'

// Dashboard
import { DashboardPage } from '@/pages/dashboard/DashboardPage'

// Workspace
import { WorkspaceListPage } from '@/pages/workspace/WorkspaceListPage'
import { WorkspaceSettingsPage } from '@/pages/workspace/WorkspaceSettingsPage'
import { NewWorkspacePage } from '@/pages/workspace/NewWorkspacePage'

// Documents
import { DocumentsPage } from '@/pages/documents/DocumentsPage'

// Chat
import { ChatPage } from '@/pages/chat/ChatPage'

// Billing
import { BillingPage } from '@/pages/billing/BillingPage'

// Settings
import { SettingsPage } from '@/pages/settings/SettingsPage'

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="flex h-full items-center justify-center text-gray-400 text-sm">
      {label} — coming soon
    </div>
  )
}

function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-bold text-gray-900">404</h1>
      <p className="text-gray-500">Page not found</p>
      <a href="/dashboard" className="text-sm text-primary-600 hover:underline">
        Go to dashboard
      </a>
    </div>
  )
}

export const router = createBrowserRouter([
  // Public auth routes
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
          { path: '/forgot-password', element: <ForgotPasswordPage /> },
        ],
      },
    ],
  },

  // Protected app routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/workspaces/new', element: <NewWorkspacePage /> },
          { path: '/workspaces', element: <WorkspaceListPage /> },
          { path: '/workspaces/:workspaceId', element: <WorkspaceSettingsPage /> },
          { path: '/workspaces/:workspaceId/settings', element: <WorkspaceSettingsPage /> },
          { path: '/documents', element: <DocumentsPage /> },
          { path: '/chat', element: <ChatPage /> },
          { path: '/billing', element: <BillingPage /> },
          { path: '/settings', element: <SettingsPage /> },
        ],
      },
    ],
  },

  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '*', element: <NotFound /> },
])
