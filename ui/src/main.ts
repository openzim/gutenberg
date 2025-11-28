import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import loadVuetify from './plugins/vuetify'

import ResizeObserver from 'resize-observer-polyfill'

if (typeof window.ResizeObserver === 'undefined') {
  window.ResizeObserver = ResizeObserver
}

loadVuetify()
  .then((vuetify) => {
    const app = createApp(App)
    app.use(createPinia())
    app.use(vuetify)
    app.use(router)
    app.mount('#app')
  })
  .catch((error) => {
    throw error
  })

