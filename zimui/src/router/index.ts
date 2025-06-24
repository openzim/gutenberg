import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import BookDetail from '@/views/BookDetail.vue'
import About from '@/views/About.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/book/:id', component: BookDetail, props: true },
  { path: '/about', component: About }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

