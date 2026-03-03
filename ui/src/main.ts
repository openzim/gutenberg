import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import loadVuetify from './plugins/vuetify'
import loadI18n, { i18nPlugin } from './plugins/i18n'

import ResizeObserver from 'resize-observer-polyfill'

if (typeof window.ResizeObserver === 'undefined') {
  window.ResizeObserver = ResizeObserver
}

Promise.all([loadI18n(), loadVuetify()])
  .then(([i18n, vuetify]) => {
    const app = createApp(App)
    const pinia = createPinia()
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
