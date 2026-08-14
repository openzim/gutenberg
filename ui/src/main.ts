import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setRouterConfig } from './router'
import { useMainStore } from './stores/main'
import loadVuetify from './plugins/vuetify'
import loadI18n, { i18nPlugin } from './plugins/i18n'

import ResizeObserver from 'resize-observer-polyfill'

if (typeof window.ResizeObserver === 'undefined') {
  window.ResizeObserver = ResizeObserver
}

const pinia = createPinia()
const mainStore = useMainStore(pinia)

mainStore
  .fetchConfig()
  .then((config) => {
    setRouterConfig(config)
    return Promise.all([loadI18n(config.source.slug), loadVuetify(config)])
  })
  .then(([i18n, vuetify]) => {
    const app = createApp(App)
    pinia.use(i18nPlugin)
    app.use(pinia)
    app.use(i18n)
    app.use(vuetify)
    app.use(router)
    app.mount('#app')
  })
  .catch((error) => {
    console.error('Failed to initialize application:', error)
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.innerHTML =
        '<div style="padding: 20px; text-align: center;">Failed to load application. Please refresh the page.</div>'
    }
  })
