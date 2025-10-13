import { useMutation, useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { billingApi } from './api'

export function usePlans() {
  return useQuery({
    queryKey: ['billing', 'plans'],
    queryFn: async () => {
      const { data } = await billingApi.listPlans()
      return data
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useSubscription(workspaceId: string) {
  return useQuery({
    queryKey: ['billing', 'subscription', workspaceId],
    queryFn: async () => {
      const { data } = await billingApi.getSubscription(workspaceId)
      return data
    },
    enabled: !!workspaceId,
  })
}

export function useUsageStats(workspaceId: string) {
  return useQuery({
    queryKey: ['billing', 'usage', workspaceId],
    queryFn: async () => {
      const { data } = await billingApi.getUsage(workspaceId)
      return data
    },
    enabled: !!workspaceId,
  })
}

export function useCreateCheckout(workspaceId: string) {
  return useMutation({
    mutationFn: (planTier: string) => billingApi.createCheckout(workspaceId, planTier),
    onSuccess: ({ data }) => {
      window.location.href = data.checkout_url
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail ?? 'Checkout failed')
    },
  })
}

export function useCreatePortal(workspaceId: string) {
  return useMutation({
    mutationFn: () => billingApi.createPortal(workspaceId),
    onSuccess: ({ data }) => {
      window.location.href = data.portal_url
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail ?? 'Could not open billing portal')
    },
  })
}
