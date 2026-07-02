import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BooksView from '../views/BooksView.vue'
import BookDetailView from '../views/BookDetailView.vue'
import AuthorListView from '../views/AuthorListView.vue'
import AuthorDetailView from '../views/AuthorDetailView.vue'
import LCCShelfListView from '../views/LCCShelfListView.vue'
import AboutView from '../views/AboutView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Home - Gutenberg Library', breadcrumb: 'nav.home' }
    },
    {
      path: '/books',
      name: 'books',
      component: BooksView,
      meta: { title: 'Books - Gutenberg Library', breadcrumb: 'nav.books' }
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: BookDetailView,
      meta: { title: 'Book Details', breadcrumb: 'nav.books', parent: '/books' }
    },
    {
      path: '/authors',
      name: 'author-list',
      component: AuthorListView,
      meta: { title: 'Authors - Gutenberg Library', breadcrumb: 'nav.authors' }
    },
    {
      path: '/author/:id',
      name: 'author-detail',
      component: AuthorDetailView,
      meta: { title: 'Author Details', breadcrumb: 'nav.authors', parent: '/authors' }
    },
    {
      path: '/lcc-shelves',
      name: 'lcc-shelf-list',
      component: LCCShelfListView,
      meta: { title: 'LCC Shelves - Gutenberg Library', breadcrumb: 'nav.shelves' }
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { title: 'About - Gutenberg Library', breadcrumb: 'nav.about' }
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
