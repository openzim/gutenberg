import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '@/views/HomePage.vue'
import BookDetail from '@/views/BookDetail.vue'
import About from '@/views/AboutPage.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/book/:id', component: BookDetail, props: true },
  { path: '/about', component: About }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
