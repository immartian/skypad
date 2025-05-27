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
  }
})
