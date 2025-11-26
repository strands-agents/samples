import { defineConfig } from 'vite'

export default defineConfig({
  // Vite configuration for browser-based Strands Agent
  server: {
    port: 5173,
    open: true
  },
  build: {
    target: 'ES2020'
  },
  define: {
    // Polyfill for Node.js globals in browser
    'process.env': JSON.stringify({})
  }
})
