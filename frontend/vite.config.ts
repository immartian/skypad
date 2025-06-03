import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  build: {
    // Ensure asset paths are relative
    assetsDir: 'assets',
    // Generate sourcemaps for better debugging
    sourcemap: true,
  },
  server: {
    // Enable host binding for Docker
    host: '0.0.0.0',
    port: 5173,
    // Enable hot reload in Docker
    watch: {
      usePolling: true,
    },
    // Proxy API calls to backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
