import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Prefer LOOMA_API_URL for proxy target in development.
// Fallbacks: VITE_PROXY_TARGET, PROXY_TARGET, default 'http://127.0.0.1:8000'
const proxyTarget = process.env.LOOMA_API_URL || process.env.VITE_PROXY_TARGET || process.env.PROXY_TARGET || 'http://127.0.0.1:8000'
console.log(proxyTarget);
export default defineConfig({
  plugins: [vue()],
  // Fine-tune dependency optimization to work around ESM/CJS interop in vue-avatar-cropper deps
  optimizeDeps: {
    // Explicitly prebundle vue-avatar-cropper and its transitive helpers so Vite creates proper ESM wrappers
    include: [
      'vue-avatar-cropper',
      'cropperjs',
      'mime/lite',
      '@babel/runtime/helpers/asyncToGenerator',
      '@babel/runtime/helpers/slicedToArray',
      '@babel/runtime/regenerator'
    ],
    force: true
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // No alias for regenerator to allow optimized ESM wrapper to be used
    }
  },
  // Build target can be overridden by environment variable
  // Preferred: LOOMA_BUILD_TARGET  (project-specific)
  // Fallback:  BUILD_TARGET        (generic)
  // Example: BUILD_TARGET=es2020 npm run build
  build: {
    target: process.env.LOOMA_BUILD_TARGET || process.env.BUILD_TARGET || 'es2019'
  },
  server: {
    host: true, // allow access from LAN (bind 0.0.0.0)
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true
      }
    }
  }
})
