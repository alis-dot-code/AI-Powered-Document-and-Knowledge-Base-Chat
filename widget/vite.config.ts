import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// IIFE bundle — single self-contained JS file with inlined CSS
export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: 'src/index.ts',
      name: 'DocMindWidget',
      fileName: 'docmind-widget',
      formats: ['iife'],
    },
    rollupOptions: {
      // Bundle React into the widget so host pages don't need it
      external: [],
    },
    cssCodeSplit: false,
    minify: true,
  },
})
