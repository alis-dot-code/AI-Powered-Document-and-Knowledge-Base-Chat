import { createProxyMiddleware, fixRequestBody } from 'http-proxy-middleware'
import { env } from '@/config/env'
import { logger } from '@/utils/logger'

/**
 * Generic proxy to FastAPI backend.
 * Preserves cookies, forwards all headers, handles JSON bodies.
 */
export const fastapiProxy = createProxyMiddleware({
  target: env.FASTAPI_URL,
  changeOrigin: true,
  // Forward the original path unchanged (routes already include /api/v1/...)
  pathRewrite: undefined,
  on: {
    error: (err, req, res) => {
      logger.error({ err, url: (req as { url?: string }).url }, 'Proxy error')
      if (!res.headersSent) {
        (res as import('http').ServerResponse).writeHead(502, { 'Content-Type': 'application/json' })
        ;(res as import('http').ServerResponse).end(
          JSON.stringify({ error: { code: 'BAD_GATEWAY', message: 'Backend unavailable' } }),
        )
      }
    },
    proxyReq: fixRequestBody,
  },
})
