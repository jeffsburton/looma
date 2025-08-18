import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Build target can be overridden by environment variable BUILD_TARGET
  // Example: BUILD_TARGET=es2020 npm run build
  build: {
    target: process.env.BUILD_TARGET || 'es2019'
  },
  server: {
    host: true, // allow access from LAN (bind 0.0.0.0)
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
