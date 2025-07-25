import { createProxyMiddleware } from 'http-proxy-middleware'
import { env } from '@/config/env'
import { logger } from '@/utils/logger'

/**
 * SSE-aware proxy — disables response buffering so tokens stream immediately.
 * Used for chat endpoints that return Server-Sent Events.
 */
export const sseProxy = createProxyMiddleware({
  target: env.FASTAPI_URL,
  changeOrigin: true,
  // Disable compression so SSE events aren't held in gzip buffer
  compress: false,
  on: {
    proxyReq: (proxyReq, req) => {
      // Signal to FastAPI that the client accepts SSE
      proxyReq.setHeader('Accept', 'text/event-stream')
      proxyReq.setHeader('Cache-Control', 'no-cache')
      proxyReq.setHeader('X-Accel-Buffering', 'no') // nginx: disable proxy buffering
    },
    proxyRes: (proxyRes, req, res) => {
      // Ensure no intermediate buffering on the gateway side
      proxyRes.headers['x-accel-buffering'] = 'no'
      proxyRes.headers['cache-control'] = 'no-cache'
    },
    error: (err, req, res) => {
      logger.error({ err }, 'SSE proxy error')
      if (!res.headersSent) {
        (res as import('http').ServerResponse).writeHead(502, { 'Content-Type': 'text/event-stream' })
        ;(res as import('http').ServerResponse).end(
          'data: {"type":"error","message":"Backend unavailable"}\n\n',
        )
      }
    },
  },
})
