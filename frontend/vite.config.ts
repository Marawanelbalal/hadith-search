import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/search': 'http://127.0.0.1:8000',
      '/hadith': 'http://127.0.0.1:8000',
      '/benchmark': 'http://127.0.0.1:8000',
      '/annotation': 'http://127.0.0.1:8000',
    },
  },
})
