import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // Fonts stay separate files, so a browser only downloads the ones a page uses.
    assetsInlineLimit: (file) => (/\.woff2?$/.test(file) ? false : undefined),
  },
  server: {
    // Same origin as the app, so the login cookie just works in development.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
