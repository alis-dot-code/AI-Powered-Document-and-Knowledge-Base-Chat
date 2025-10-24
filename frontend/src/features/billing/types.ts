export interface PlanInfo {
  tier: string
  name: string
  price_monthly: number
  query_limit: number
  document_limit: number
  members_limit: number
  features: string[]
}

export interface Subscription {
  id: string
  workspace_id: string
  plan_tier: string
  status: string
  stripe_subscription_id: string | null
  current_period_start: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  created_at: string
  updated_at: string
}

export interface UsageStats {
  queries_used: number
  queries_limit: number
  documents_used: number
  documents_limit: number
  period_start: string | null
  period_end: string | null
}
