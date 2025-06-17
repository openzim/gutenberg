// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  server: {
    watch: {
      usePolling: true,
    
      interval: 100,
    },
    
    host: '0.0.0.0',
   
  }
})
