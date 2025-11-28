import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify from 'vite-plugin-vuetify';
import legacy from '@vitejs/plugin-legacy';
// https://vitejs.dev/config/
export default defineConfig({
    base: './',
    plugins: [
        vue(),
        vuetify({ autoImport: true }),
        legacy({
            targets: ['fully supports es6'],
            modernPolyfills: true
        })
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    build: {
        chunkSizeWarningLimit: 1000
    },
    server: {
        port: 5173
    },
    preview: {
        port: 5173
    }
});
