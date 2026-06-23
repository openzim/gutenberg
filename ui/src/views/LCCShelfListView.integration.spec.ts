/**
 * Integration tests for LCCShelfListView
 * Tests LCC shelf browsing with sidebar selection and book display
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LCCShelfListView from './LCCShelfListView.vue'
import { useMainStore } from '@/stores/main'
import type { LCCShelves, BookPreview } from '@/types'

const mockShelvesData: LCCShelves = {
  totalCount: 4,
  shelves: [
    { code: 'PR', name: 'English literature', bookCount: 150 },
    { code: 'PS', name: 'American literature', bookCount: 200 },
    { code: 'PQ', name: 'French literature', bookCount: 100 },
    { code: 'PT', name: 'German literature', bookCount: 80 }
  ]
}

const mockBooks: BookPreview[] = [
  {
    id: 1,
    title: 'Alice in Wonderland',
    author: { id: '1', name: 'Lewis Carroll', bookCount: 1 },
    languages: ['en'],
    popularity: 5,
    coverPath: null,
    lccShelf: null
  },
  {
    id: 2,
    title: 'Pride and Prejudice',
    author: { id: '2', name: 'Jane Austen', bookCount: 1 },
    languages: ['en'],
    popularity: 4,
    coverPath: null,
    lccShelf: null
  }
]

describe('LCCShelfListView Integration', () => {
  let router: ReturnType<typeof createRouter>
  let store: ReturnType<typeof useMainStore>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useMainStore()
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/lcc-shelves', component: LCCShelfListView }]
    })
  })

  const mountView = async (
    shelvesData: LCCShelves = mockShelvesData,
    books: BookPreview[] = mockBooks,
    shelfQuery?: string
  ) => {
    vi.spyOn(store, 'fetchLCCShelves').mockResolvedValue(shelvesData)
    vi.spyOn(store, 'fetchLCCShelf').mockResolvedValue({
      code: 'PR',
      name: 'English literature',
      bookCount: books.length,
      books
    })
    vi.spyOn(store, 'fetchBooks').mockResolvedValue({ totalCount: books.length, books })

    await router.push({ path: '/lcc-shelves', query: shelfQuery ? { shelf: shelfQuery } : {} })
    await router.isReady()

    const wrapper = mount(LCCShelfListView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads shelves on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchLCCShelves).toHaveBeenCalledOnce()
      expect(wrapper.find('.lcc-sidebar').exists()).toBe(true)
    })

    it('loads all books when no shelf is selected', async () => {
      const wrapper = await mountView()

      await flushPromises()
      expect(store.fetchBooks).toHaveBeenCalled()
      expect(wrapper.find('.books-grid').exists()).toBe(true)
    })
  })

  describe('Shelf Selection', () => {
    it('loads shelf books when a shelf is selected', async () => {
      await mountView(mockShelvesData, mockBooks, 'PR')

      await flushPromises()
      expect(store.fetchLCCShelf).toHaveBeenCalledWith('PR')
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no books available', async () => {
      const wrapper = await mountView(mockShelvesData, [])

      await flushPromises()
      expect(wrapper.findComponent({ name: 'EmptyState' }).exists()).toBe(true)
    })
  })
})
