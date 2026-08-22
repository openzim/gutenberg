/**
 * Integration tests for CollectionListView
 * Tests collection browsing with sidebar selection and book display
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import CollectionListView from './CollectionListView.vue'
import { useMainStore } from '@/stores/main'
import type { Collection, Collections, BookPreview } from '@/types'

const mockCollectionsData: Collections = {
  totalCount: 4,
  collections: [
    { id: 'PR', name: 'English literature', bookCount: 150, totalPopularity: 0 },
    { id: 'PS', name: 'American literature', bookCount: 200, totalPopularity: 0 },
    { id: 'PQ', name: 'French literature', bookCount: 100, totalPopularity: 0 },
    { id: 'PT', name: 'German literature', bookCount: 80, totalPopularity: 0 }
  ]
}

const mockBooks: BookPreview[] = [
  {
    id: '1',
    title: 'Alice in Wonderland',
    author: { id: '1', name: 'Lewis Carroll', bookCount: 1 },
    languages: ['en'],
    popularity: 5,
    coverPath: null,
    primaryCollection: null
  },
  {
    id: '2',
    title: 'Pride and Prejudice',
    author: { id: '2', name: 'Jane Austen', bookCount: 1 },
    languages: ['en'],
    popularity: 4,
    coverPath: null,
    primaryCollection: null
  }
]

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

describe('CollectionListView Integration', () => {
  let router: ReturnType<typeof createRouter>
  let store: ReturnType<typeof useMainStore>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useMainStore()
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/collections', component: CollectionListView }]
    })
  })

  const mountView = async (
    collectionsData: Collections = mockCollectionsData,
    books: BookPreview[] = mockBooks,
    collectionQuery?: string
  ) => {
    vi.spyOn(store, 'fetchCollections').mockResolvedValue(collectionsData)
    vi.spyOn(store, 'fetchCollection').mockResolvedValue({
      id: 'PR',
      name: 'English literature',
      bookCount: books.length,
      totalPopularity: 0,
      books
    })
    vi.spyOn(store, 'fetchBooks').mockResolvedValue({ totalCount: books.length, books })

    await router.push({
      path: '/collections',
      query: collectionQuery ? { collection: collectionQuery } : {}
    })
    await router.isReady()

    const wrapper = mount(CollectionListView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads collections on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchCollections).toHaveBeenCalledOnce()
      expect(wrapper.find('.collection-sidebar').exists()).toBe(true)
    })

    it('loads all books when no collection is selected', async () => {
      const wrapper = await mountView()

      await flushPromises()
      expect(store.fetchBooks).toHaveBeenCalledOnce()
      expect(wrapper.find('.books-grid').exists()).toBe(true)
    })

    it('uses the actual book total instead of summing collection memberships', async () => {
      const wrapper = await mountView()

      expect(wrapper.find('.collection-sidebar__count').text()).toBe('(2)')
    })
  })

  describe('Collection Selection', () => {
    it('loads collection books when a collection is selected', async () => {
      await mountView(mockCollectionsData, mockBooks, 'PR')

      await flushPromises()
      expect(store.fetchCollection).toHaveBeenCalledWith('PR')
      expect(store.fetchBooks).toHaveBeenCalled()
    })

    it('ignores a late response for a previously selected collection', async () => {
      const firstCollection = deferred<Collection>()
      const secondCollection = deferred<Collection>()
      vi.spyOn(store, 'fetchCollections').mockResolvedValue(mockCollectionsData)
      vi.spyOn(store, 'fetchBooks').mockResolvedValue({
        totalCount: mockBooks.length,
        books: mockBooks
      })
      vi.spyOn(store, 'fetchCollection').mockImplementation((id) =>
        id === 'PR' ? firstCollection.promise : secondCollection.promise
      )

      await router.push({ path: '/collections', query: { collection: 'PR' } })
      await router.isReady()
      const wrapper = mount(CollectionListView, {
        global: { plugins: [pinia, router] }
      })
      await flushPromises()

      await router.push({ path: '/collections', query: { collection: 'PS' } })
      await flushPromises()

      secondCollection.resolve({
        id: 'PS',
        name: 'American literature',
        bookCount: 1,
        totalPopularity: 0,
        books: [{ ...mockBooks[0]!, title: 'Current collection book' }]
      })
      await flushPromises()

      firstCollection.resolve({
        id: 'PR',
        name: 'English literature',
        bookCount: 1,
        totalPopularity: 0,
        books: [{ ...mockBooks[1]!, title: 'Stale collection book' }]
      })
      await flushPromises()

      expect(wrapper.text()).toContain('Current collection book')
      expect(wrapper.text()).not.toContain('Stale collection book')
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no books available', async () => {
      const wrapper = await mountView(mockCollectionsData, [])

      await flushPromises()
      expect(wrapper.findComponent({ name: 'EmptyState' }).exists()).toBe(true)
    })
  })
})
