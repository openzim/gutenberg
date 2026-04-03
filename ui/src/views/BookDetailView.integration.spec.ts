/**
 * Integration tests for BookDetailView
 * Tests book detail page with data loading and navigation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import BookDetailView from './BookDetailView.vue'
import { useMainStore } from '@/stores/main'
import type { Book } from '@/types'

const mockBookData: Book = {
  id: 1,
  title: 'Pride and Prejudice',
  author: {
    id: 'austen-jane',
    name: 'Jane Austen',
    firstName: 'Jane',
    lastName: 'Austen',
    birthYear: '1775',
    deathYear: '1817'
  },
  languages: ['en'],
  popularity: 5,
  coverPath: '/covers/1.jpg',
  lccShelf: 'PR',
  subtitle: null,
  license: 'Public domain',
  downloads: 50000,
  description: 'A classic novel of manners',
  formats: [
    { format: 'html', path: 'https://example.com/1.html', available: true },
    { format: 'epub', path: 'https://example.com/1.epub', available: true },
    { format: 'pdf', path: 'https://example.com/1.pdf', available: true }
  ]
}

describe('BookDetailView Integration', () => {
  let router: ReturnType<typeof createRouter>
  let store: ReturnType<typeof useMainStore>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useMainStore()
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/book/:id', name: 'book-detail', component: BookDetailView },
        { path: '/author/:id', name: 'author-detail', component: { template: '<div>Author</div>' } }
      ]
    })
  })

  const mountView = async (bookId: string = '1') => {
    vi.spyOn(store, 'fetchBook').mockResolvedValue(mockBookData)
    router.push(`/book/${bookId}`)
    await router.isReady()

    const wrapper = mount(BookDetailView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads and displays book details on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchBook).toHaveBeenCalledWith(1)
      expect(wrapper.text()).toContain('Pride and Prejudice')
      expect(wrapper.text()).toContain('Jane Austen')
    })

    it('handles different book IDs from route params', async () => {
      await mountView('42')

      expect(store.fetchBook).toHaveBeenCalledWith(42)
    })
  })

  describe('Book Information Display', () => {
    it('displays book detail info component with correct props', async () => {
      const wrapper = await mountView()

      const detailInfo = wrapper.findComponent({ name: 'BookDetailInfo' })
      expect(detailInfo.exists()).toBe(true)
      expect(detailInfo.props('book')).toEqual(mockBookData)
    })

    it('displays book cover image', async () => {
      const wrapper = await mountView()

      const coverImage = wrapper.findComponent({ name: 'BookCoverImage' })
      expect(coverImage.exists()).toBe(true)
      expect(coverImage.props('coverPath')).toBe('/covers/1.jpg')
      expect(coverImage.props('alt')).toBe('Pride and Prejudice cover')
    })
  })

  describe('Navigation', () => {
    it('provides link to author detail page', async () => {
      const wrapper = await mountView()

      const authorLink = wrapper.find('a[href*="author"]')
      expect(authorLink.exists()).toBe(true)
    })

    it('has breadcrumbs navigation', async () => {
      const wrapper = await mountView()

      const breadcrumbs = wrapper.findComponent({ name: 'Breadcrumbs' })
      expect(breadcrumbs.exists()).toBe(true)
    })
  })

  describe('Download Formats', () => {
    it('displays available download formats', async () => {
      const wrapper = await mountView()

      expect(wrapper.text()).toContain('EPUB')
      expect(wrapper.text()).toContain('PDF')
    })
  })

  describe('Error Handling', () => {
    it('handles fetch errors gracefully', async () => {
      vi.spyOn(store, 'fetchBook').mockRejectedValue(new Error('Book not found'))
      router.push('/book/1')
      await router.isReady()

      const wrapper = mount(BookDetailView, {
        global: { plugins: [router] }
      })
      await flushPromises()

      const notFoundState = wrapper.findComponent({ name: 'NotFoundState' })
      expect(notFoundState.exists()).toBe(true)

      const bookDetailInfo = wrapper.findComponent({ name: 'BookDetailInfo' })
      expect(bookDetailInfo.exists()).toBe(false)
    })
  })
})
