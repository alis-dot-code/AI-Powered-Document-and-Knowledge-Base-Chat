import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Check, CreditCard, ExternalLink, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { useGlobalStore } from '@/stores/global'
import {
  usePlans,
  useSubscription,
  useUsageStats,
  useCreateCheckout,
  useCreatePortal,
} from '@/features/billing/hooks'
import { cn } from '@/lib/utils'

function UsageBar({ used, limit, label }: { used: number; limit: number; label: string }) {
  const pct = Math.min((used / limit) * 100, 100)
  const color = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-primary-500'
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>{label}</span>
        <span className="font-medium">{used.toLocaleString()} / {limit.toLocaleString()}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div className={cn('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function BillingPage() {
  const { activeWorkspaceId } = useGlobalStore()
  const [searchParams] = useSearchParams()

  const { data: plans, isLoading: plansLoading } = usePlans()
  const { data: subscription } = useSubscription(activeWorkspaceId ?? '')
  const { data: usage } = useUsageStats(activeWorkspaceId ?? '')
  const checkout = useCreateCheckout(activeWorkspaceId ?? '')
  const portal = useCreatePortal(activeWorkspaceId ?? '')

  useEffect(() => {
    if (searchParams.get('success') === '1') {
      toast.success('Subscription activated!')
    }
  }, [searchParams])

  if (!activeWorkspaceId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        Select a workspace to manage billing.
      </div>
    )
  }

  const currentTier = subscription?.plan_tier ?? 'free'
  const isActive = subscription?.status === 'active' || subscription?.status === 'trialing'

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Billing & Usage</h1>
          <p className="mt-1 text-sm text-gray-500">Manage your plan and monitor usage.</p>
        </div>

        {/* Current plan summary */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Current Plan</p>
              <p className="mt-1 text-2xl font-bold capitalize text-gray-900">{currentTier}</p>
              {subscription?.current_period_end && (
                <p className="mt-0.5 text-xs text-gray-500">
                  Renews {new Date(subscription.current_period_end).toLocaleDateString()}
                  {subscription.cancel_at_period_end && ' · Cancels at period end'}
                </p>
              )}
            </div>
            {currentTier !== 'free' && (
              <button
                onClick={() => portal.mutate()}
                disabled={portal.isPending}
                className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
              >
                <CreditCard className="h-3.5 w-3.5" />
                Manage Billing
                <ExternalLink className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Usage stats */}
        {usage && (
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-gray-900">This Period's Usage</h2>
            <div className="space-y-4">
              <UsageBar used={usage.queries_used} limit={usage.queries_limit} label="Queries" />
              <UsageBar used={usage.documents_used} limit={usage.documents_limit} label="Documents" />
            </div>
            {usage.period_start && usage.period_end && (
              <p className="mt-3 text-xs text-gray-400">
                {new Date(usage.period_start).toLocaleDateString()} –{' '}
                {new Date(usage.period_end).toLocaleDateString()}
              </p>
            )}
          </div>
        )}

        {/* Plan cards */}
        <div>
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Plans</h2>
          {plansLoading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-64 animate-pulse rounded-xl bg-gray-100" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {plans?.map((plan) => {
                const isCurrent = plan.tier === currentTier
                const isPopular = plan.tier === 'pro'
                return (
                  <div
                    key={plan.tier}
                    className={cn(
                      'relative flex flex-col rounded-xl border p-5 shadow-sm',
                      isCurrent
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 bg-white'
                    )}
                  >
                    {isPopular && (
                      <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 rounded-full bg-primary-600 px-3 py-0.5 text-xs font-semibold text-white">
                        Popular
                      </span>
                    )}
                    <div className="mb-4">
                      <p className="font-semibold text-gray-900">{plan.name}</p>
                      <p className="mt-1">
                        <span className="text-2xl font-bold text-gray-900">
                          ${plan.price_monthly}
                        </span>
                        <span className="text-xs text-gray-400">/mo</span>
                      </p>
                    </div>
                    <ul className="mb-5 flex-1 space-y-2">
                      {plan.features.map((f) => (
                        <li key={f} className="flex items-start gap-2 text-xs text-gray-600">
                          <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary-600" />
                          {f}
                        </li>
                      ))}
                      <li className="flex items-start gap-2 text-xs text-gray-600">
                        <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary-600" />
                        {plan.query_limit.toLocaleString()} queries/mo
                      </li>
                      <li className="flex items-start gap-2 text-xs text-gray-600">
                        <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary-600" />
                        {plan.document_limit} documents
                      </li>
                    </ul>
                    {isCurrent ? (
                      <span className="block rounded-lg bg-primary-600 py-2 text-center text-xs font-semibold text-white">
                        Current Plan
                      </span>
                    ) : plan.tier === 'free' ? (
                      <span className="block rounded-lg border border-gray-200 py-2 text-center text-xs font-medium text-gray-400">
                        Free
                      </span>
                    ) : (
                      <button
                        onClick={() => checkout.mutate(plan.tier)}
                        disabled={checkout.isPending}
                        className="flex items-center justify-center gap-1.5 rounded-lg bg-primary-600 py-2 text-xs font-semibold text-white hover:bg-primary-700 disabled:opacity-50"
                      >
                        <Zap className="h-3.5 w-3.5" />
                        Upgrade
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
