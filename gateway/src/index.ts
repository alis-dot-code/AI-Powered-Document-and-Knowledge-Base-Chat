import { redis } from '@/config/redis'
import { env } from '@/config/env'
import { logger } from '@/utils/logger'
import app from '@/app'

async function main() {
  // Ensure Redis is connected before accepting traffic
  await redis.connect()

  const server = app.listen(env.PORT, () => {
    logger.info(`Gateway running on http://localhost:${env.PORT} [${env.NODE_ENV}]`)
    logger.info(`Proxying to FastAPI at ${env.FASTAPI_URL}`)
  })

  // Graceful shutdown
  const shutdown = async (signal: string) => {
    logger.info(`Received ${signal} — shutting down gracefully`)
    server.close(async () => {
      await redis.quit()
      logger.info('Gateway stopped')
      process.exit(0)
    })
    setTimeout(() => process.exit(1), 10_000)
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'))
  process.on('SIGINT', () => shutdown('SIGINT'))
}

main().catch((err) => {
  logger.error({ err }, 'Fatal startup error')
  process.exit(1)
})
