import { createRouter, createWebHashHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView }
  ],
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  }
})

export default router

