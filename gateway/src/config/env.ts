import { z } from 'zod'
import dotenv from 'dotenv'
dotenv.config()

const schema = z.object({
  PORT: z.coerce.number().default(3000),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  FASTAPI_URL: z.string().url().default('http://localhost:8000'),
  REDIS_URL: z.string().default('redis://localhost:6379/0'),
  JWT_SECRET_KEY: z.string().min(32),
  JWT_ALGORITHM: z.string().default('HS256'),
  ALLOWED_ORIGINS: z.string().default('http://localhost:5173'),
  RATE_LIMIT_WINDOW_MS: z.coerce.number().default(60_000),
  RATE_LIMIT_MAX_REQUESTS: z.coerce.number().default(100),
})

const parsed = schema.safeParse(process.env)
if (!parsed.success) {
  console.error('❌ Invalid environment variables:\n', parsed.error.format())
  process.exit(1)
}

export const env = parsed.data
export type Env = typeof env
