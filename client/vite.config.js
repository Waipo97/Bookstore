import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // everything that belongs to the Django backend is proxied to it
    proxy: {
      '/api': 'http://localhost:8000',
      '/media': 'http://localhost:8000', // uploaded pictures
      '/admin': 'http://localhost:8000', // lets the front end open the admin panel
      '/static': 'http://localhost:8000', // css/js of the admin panel
    },
  },
})
