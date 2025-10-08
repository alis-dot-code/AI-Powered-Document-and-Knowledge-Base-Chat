import { redis } from '@/config/redis'
import { QuotaExceededError } from '@/utils/errors'

// Plan limits — mirrors backend PLANS definition
const PLAN_LIMITS: Record<string, { queries: number; documents: number }> = {
  free: { queries: 50, documents: 10 },
  pro: { queries: 1000, documents: 100 },
  team: { queries: 5000, documents: 500 },
}

// Keys: usage:<workspaceId>:<YYYY-MM>:<type>
function usageKey(workspaceId: string, type: 'queries' | 'documents'): string {
  const period = new Date().toISOString().slice(0, 7) // YYYY-MM
  return `usage:${workspaceId}:${period}:${type}`
}

function planKey(workspaceId: string): string {
  return `plan:${workspaceId}`
}

export async function cachePlanTier(workspaceId: string, tier: string): Promise<void> {
  await redis.set(planKey(workspaceId), tier, 'EX', 3600) // 1h TTL
}

export async function getPlanTier(workspaceId: string): Promise<string> {
  const cached = await redis.get(planKey(workspaceId))
  return cached || 'free'
}

export async function incrementQueryCount(workspaceId: string): Promise<number> {
  const key = usageKey(workspaceId, 'queries')
  const count = await redis.incr(key)
  if (count === 1) {
    await redis.expire(key, 35 * 86400)
  }
  return count
}

export async function incrementDocumentCount(workspaceId: string): Promise<number> {
  const key = usageKey(workspaceId, 'documents')
  const count = await redis.incr(key)
  if (count === 1) {
    await redis.expire(key, 35 * 86400)
  }
  return count
}

export async function checkQueryLimit(workspaceId: string, limit?: number): Promise<void> {
  const tier = await getPlanTier(workspaceId)
  const max = limit ?? PLAN_LIMITS[tier]?.queries ?? 50
  const key = usageKey(workspaceId, 'queries')
  const raw = await redis.get(key)
  const count = raw ? parseInt(raw, 10) : 0
  if (count >= max) {
    throw new QuotaExceededError('queries')
  }
}

export async function checkDocumentLimit(workspaceId: string, limit?: number): Promise<void> {
  const tier = await getPlanTier(workspaceId)
  const max = limit ?? PLAN_LIMITS[tier]?.documents ?? 10
  const key = usageKey(workspaceId, 'documents')
  const raw = await redis.get(key)
  const count = raw ? parseInt(raw, 10) : 0
  if (count >= max) {
    throw new QuotaExceededError('documents')
  }
}

export async function getQueryCount(workspaceId: string): Promise<number> {
  const key = usageKey(workspaceId, 'queries')
  const raw = await redis.get(key)
  return raw ? parseInt(raw, 10) : 0
}

export async function getDocumentCount(workspaceId: string): Promise<number> {
  const key = usageKey(workspaceId, 'documents')
  const raw = await redis.get(key)
  return raw ? parseInt(raw, 10) : 0
}
