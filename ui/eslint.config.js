import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettierSkipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default [
  // Files linted: **/*.{js,mjs,cjs,ts,mts,tsx,vue}
  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**', '**/*.d.ts'],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential'],

  {
    name: 'app/vue-typescript-setup',
    files: ['**/*.vue'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        parser: tseslint.parser,
      },
      globals: {
        console: 'readonly',
      },
    },
  },

  prettierSkipFormatting,
]
