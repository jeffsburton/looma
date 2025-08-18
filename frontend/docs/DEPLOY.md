# Deploying the Vite/Vue Frontend

This project uses Vite with Vue 3. To produce a production build and deploy it, follow the steps below.

Prerequisites
- Node.js 18+ (recommend LTS). Check with: node -v
- npm 9+ (comes with Node). Check with: npm -v

Install dependencies
- From the frontend directory:
  - npm ci  # preferred for clean installs (or use `npm install`)

Build for production
- npm run build
- Output: frontend/dist

Preview the production build locally (optional)
- npm run preview
- Opens a local server that serves the built dist/ for quick validation.

How to deploy the built files
Option A: Serve via the FastAPI backend (simple, one-process)
1) Build as above (dist/ is created).
2) Set environment variable when running the backend:
   - SERVE_FRONTEND=true
3) Start the backend (Uvicorn, Docker, etc.). If frontend/dist exists, the backend will serve it at the root path / and keep API at /api/v1.

Option B: Serve with a static web server or CDN (e.g., Nginx, Netlify, GitHub Pages)
- Upload the contents of frontend/dist to your host.
- Ensure your server is configured to serve index.html for unknown routes (SPA fallback). For Nginx:
  ```
  location / {
      try_files $uri /index.html;
  }
  ```
- If deploying under a subpath (e.g., https://example.com/app/), set the base path in Vite before building. In vite.config.js:
  ```js
  export default defineConfig({
    base: '/app/',
    plugins: [vue()],
  })
  ```
  Then re-run npm run build.

Common commands (Windows PowerShell)
- cd .\frontend
- npm ci
- npm run build
- npm run preview

Troubleshooting
- Blank page after deploy: likely a base path mismatch. Configure `base` in vite.config.js if not deploying at site root.
- API calls failing in production: ensure your frontend uses the correct API URL (e.g., environment config) and your server CORS is set appropriately if serving from a different origin.

Notes
- Dev proxy in vite.config.js only affects development (npm run dev). In production, calls go directly to the URLs you program in the frontend code.
