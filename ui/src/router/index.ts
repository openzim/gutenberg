import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BookDetailView from '../views/BookDetailView.vue'
import AuthorListView from '../views/AuthorListView.vue'
import AuthorDetailView from '../views/AuthorDetailView.vue'
import LCCShelfListView from '../views/LCCShelfListView.vue'
import LCCShelfDetailView from '../views/LCCShelfDetailView.vue'
import AboutView from '../views/AboutView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Home - Gutenberg Library' }
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: BookDetailView,
      meta: { title: 'Book Details' }
    },
    {
      path: '/authors',
      name: 'author-list',
      component: AuthorListView,
      meta: { title: 'Authors - Gutenberg Library' }
    },
    {
      path: '/author/:id',
      name: 'author-detail',
      component: AuthorDetailView,
      meta: { title: 'Author Details' }
    },
    {
      path: '/lcc-shelves',
      name: 'lcc-shelf-list',
      component: LCCShelfListView,
      meta: { title: 'LCC Shelves - Gutenberg Library' }
    },
    {
      path: '/lcc-shelf/:code',
      name: 'lcc-shelf-detail',
      component: LCCShelfDetailView,
      meta: { title: 'LCC Shelf Details' }
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { title: 'About - Gutenberg Library' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: { title: 'Page Not Found' }
    }
  ],
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  }
})

router.beforeEach((to, _from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router
