import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// VITE_BACKEND_URL or VITE_API_URL is set in Vercel environment variables.
// In local dev, the proxy below handles /api and /health automatically.
const BACKEND_URL = process.env.VITE_BACKEND_URL || process.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],

  // Expose VITE_BACKEND_URL to the React app at build time
  define: {
    __BACKEND_URL__: JSON.stringify(BACKEND_URL),
  },

  server: {
    port: 5173,
    // Dev proxy — only active during `npm run dev`
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
