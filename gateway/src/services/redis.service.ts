import { redis } from '@/config/redis'

export async function setWithExpiry(key: string, value: string, ttlSeconds: number): Promise<void> {
  await redis.set(key, value, 'EX', ttlSeconds)
}

export async function get(key: string): Promise<string | null> {
  return redis.get(key)
}

export async function del(key: string): Promise<void> {
  await redis.del(key)
}

export async function increment(key: string, ttlSeconds?: number): Promise<number> {
  const val = await redis.incr(key)
  if (ttlSeconds && val === 1) {
    await redis.expire(key, ttlSeconds)
  }
  return val
}

export async function isHealthy(): Promise<boolean> {
  try {
    await redis.ping()
    return true
  } catch {
    return false
  }
}
