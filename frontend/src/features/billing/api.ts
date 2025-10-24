import api from '@/lib/axios'
import type { PlanInfo, Subscription, UsageStats } from './types'

export const billingApi = {
  listPlans: () =>
    api.get<PlanInfo[]>('/billing/plans'),

  getSubscription: (workspaceId: string) =>
    api.get<Subscription>(`/billing/workspaces/${workspaceId}/subscription`),

  createCheckout: (workspaceId: string, planTier: string) =>
    api.post<{ checkout_url: string }>(`/billing/workspaces/${workspaceId}/checkout`, {
      plan_tier: planTier,
      success_url: `${window.location.origin}/billing?success=1`,
      cancel_url: `${window.location.origin}/billing`,
    }),

  createPortal: (workspaceId: string) =>
    api.post<{ portal_url: string }>(`/billing/workspaces/${workspaceId}/portal`),

  getUsage: (workspaceId: string) =>
    api.get<UsageStats>(`/billing/workspaces/${workspaceId}/usage`),
}
