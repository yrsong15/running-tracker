import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // API_PROXY lets a second checkout point at its own backend port.
    proxy: { '/api': process.env.API_PROXY ?? 'http://127.0.0.1:8000' },
  },
})
