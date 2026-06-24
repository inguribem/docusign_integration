import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/contracts': 'http://localhost:8000',
      '/templates': 'http://localhost:8000',
      '/config':    'http://localhost:8000',
    },
  },
})
