import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Same origin as the app, so the login cookie just works in development.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
