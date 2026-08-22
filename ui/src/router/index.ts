import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BooksView from '../views/BooksView.vue'
import BookDetailView from '../views/BookDetailView.vue'
import AuthorListView from '../views/AuthorListView.vue'
import AuthorDetailView from '../views/AuthorDetailView.vue'
import CollectionListView from '../views/CollectionListView.vue'
import AboutView from '../views/AboutView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import type { Config } from '@/types'

let config: Config | null = null

export function setRouterConfig(nextConfig: Config) {
  config = nextConfig
}

function routeTitle(routeName: string): string {
  const labels = config?.theme.routeLabels
  const label = labels?.[routeName] || routeName
  return config ? `${label} - ${config.title}` : `${label} - Library`
}

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { breadcrumb: 'nav.home' }
    },
    {
      path: '/books',
      name: 'books',
      component: BooksView,
      meta: { breadcrumb: 'nav.books' }
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: BookDetailView,
      meta: { breadcrumb: 'nav.books', parent: '/books' }
    },
    {
      path: '/authors',
      name: 'author-list',
      component: AuthorListView,
      meta: { breadcrumb: 'nav.authors' }
    },
    {
      path: '/author/:id',
      name: 'author-detail',
      component: AuthorDetailView,
      meta: { breadcrumb: 'nav.authors', parent: '/authors' }
    },
    {
      path: '/collections',
      name: 'collection-list',
      component: CollectionListView,
      meta: { breadcrumb: 'nav.collections' }
    },
    {
      path: '/collections',
      redirect: '/collections'
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { breadcrumb: 'nav.about' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: {}
    }
  ],
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  }
})

router.beforeEach((to, _from, next) => {
  document.title = routeTitle(
    to.name === 'collection-list' ? 'collections' : String(to.name || 'home')
  )
  next()
})

export default router
