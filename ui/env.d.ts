/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@wikimedia/language-data' {
  function getAutonym(code: string): string
  function isRtl(code: string): boolean
  function isKnown(code: string): boolean
  function getScript(code: string): string
  function getDir(code: string): string
  function getLanguages(): Record<string, unknown[]>
  export default {
    getAutonym,
    isRtl,
    isKnown,
    getScript,
    getDir,
    getLanguages
  }
}
