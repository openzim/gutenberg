import { fileURLToPath, URL } from 'node:url';
import { cp } from 'node:fs/promises';
import { join } from 'node:path';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify from 'vite-plugin-vuetify';
import legacy from '@vitejs/plugin-legacy';
function copyPdfJsAssets() {
    let outputDir = '';
    let copied = false;
    const pdfjsDir = fileURLToPath(new URL('./node_modules/pdfjs-dist/', import.meta.url));
    return {
        name: 'copy-pdfjs-assets',
        configResolved(config) {
            outputDir = config.build.outDir;
        },
        async writeBundle() {
            if (copied)
                return;
            copied = true;
            await Promise.all(['cmaps', 'standard_fonts'].map((directory) => cp(join(pdfjsDir, directory), join(outputDir, 'pdfjs', directory), {
                recursive: true
            })));
        }
    };
}
// https://vitejs.dev/config/
export default defineConfig({
    base: './',
    plugins: [
        vue({
            template: {
                compilerOptions: {
                    isCustomElement: (tag) => tag === 'foliate-view'
                }
            }
        }),
        vuetify({ autoImport: true }),
        copyPdfJsAssets(),
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
