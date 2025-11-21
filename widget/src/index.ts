/**
 * DocMind embeddable widget — IIFE bundle.
 *
 * Usage (add to any HTML page):
 *   <script src="https://cdn.docmind.ai/widget/docmind-widget.iife.js"></script>
 *   <script>
 *     DocMindWidget.init({
 *       apiKey: 'dm_live_xxxxxxxxxxxx',
 *       gatewayUrl: 'https://api.yourapp.com',  // optional, defaults to localhost:3000
 *     })
 *   </script>
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { Widget } from './Widget'
import './styles.css'

interface InitOptions {
  apiKey: string
  gatewayUrl?: string
  containerId?: string
}

function init(options: InitOptions): void {
  const { apiKey, gatewayUrl, containerId } = options

  if (!apiKey) {
    console.error('[DocMind Widget] apiKey is required')
    return
  }

  // Allow api.ts to pick up the gatewayUrl at runtime
  ;(window as any).DocMindWidget = { _gatewayUrl: gatewayUrl ?? 'http://localhost:3000' }

  let container: HTMLElement | null = null
  if (containerId) {
    container = document.getElementById(containerId)
    if (!container) {
      console.error(`[DocMind Widget] Container #${containerId} not found`)
      return
    }
  } else {
    container = document.createElement('div')
    container.id = 'docmind-widget-root'
    document.body.appendChild(container)
  }

  ReactDOM.createRoot(container).render(
    React.createElement(Widget, { apiKey, gatewayUrl })
  )
}

// Expose on window
;(window as any).DocMindWidget = { init }
