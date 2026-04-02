import { mergeConfig } from 'vite';
import { defineConfig } from 'vitest/config';
import viteConfig from './vite.config';
export default mergeConfig(viteConfig, defineConfig({
    test: {
        environment: 'jsdom',
        setupFiles: ['./vitest.setup.ts'],
        server: {
            deps: {
                inline: ['vuetify'],
            },
        },
    },
}));
