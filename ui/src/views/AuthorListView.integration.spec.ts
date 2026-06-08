/**
 * Integration tests for AuthorListView
 * Tests author browsing with alphabet filter and infinite scroll
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AuthorListView from './AuthorListView.vue'
import { useMainStore } from '@/stores/main'
import type { Authors } from '@/types'

const mockAuthorsData: Authors = {
  totalCount: 5,
  authors: [
    { id: 'austen-jane', name: 'Jane Austen', bookCount: 6 },
    { id: 'dickens-charles', name: 'Charles Dickens', bookCount: 15 },
    { id: 'shakespeare-william', name: 'William Shakespeare', bookCount: 20 },
    { id: 'hugo-victor', name: 'Victor Hugo', bookCount: 10 },
    { id: 'twain-mark', name: 'Mark Twain', bookCount: 12 }
  ]
}

describe('AuthorListView Integration', () => {
  let router: ReturnType<typeof createRouter>
  let store: ReturnType<typeof useMainStore>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useMainStore()
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/authors', component: AuthorListView }]
    })
  })

  const mountView = async (mockData: Authors = mockAuthorsData) => {
    vi.spyOn(store, 'fetchAuthors').mockResolvedValue(mockData)
    const wrapper = mount(AuthorListView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads and displays authors on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchAuthors).toHaveBeenCalledOnce()
      expect(wrapper.text()).toContain('Jane Austen')
      expect(wrapper.text()).toContain('Charles Dickens')
      expect(wrapper.text()).toContain('William Shakespeare')
    })

    it('shows empty state when no authors available', async () => {
      const wrapper = await mountView({ totalCount: 0, authors: [] })

      expect(wrapper.text()).toContain('No authors found')
    })
  })

  describe('Alphabet Filter', () => {
    it('filters authors by letter', async () => {
      const wrapper = await mountView()

      const filter = wrapper.findComponent({ name: 'AlphabetFilter' })
      expect(filter.exists()).toBe(true)

      // Click on 'J' filter
      const jButton = filter.findAll('.alphabet-btn').find((btn) => btn.text().includes('J'))
      expect(jButton).toBeDefined()
      await jButton!.trigger('click')
      await flushPromises()

      const authorsList = wrapper.findComponent({ name: 'AuthorsList' })
      expect(authorsList.props('authors')).toHaveLength(1)
      expect(authorsList.props('authors')[0].name).toBe('Jane Austen')
    })

    it('switches back to ALL showing all authors', async () => {
      const wrapper = await mountView()

      const filter = wrapper.findComponent({ name: 'AlphabetFilter' })

      // Click on 'J' filter
      const jButton = filter.findAll('.alphabet-btn').find((btn) => btn.text().includes('J'))
      await jButton!.trigger('click')
      await flushPromises()

      const authorsList = wrapper.findComponent({ name: 'AuthorsList' })
      expect(authorsList.props('authors')).toHaveLength(1)

      // Click back to ALL
      const allButton = filter.findAll('.alphabet-btn').find((btn) => btn.text().includes('ALL'))
      await allButton!.trigger('click')
      await flushPromises()

      expect(authorsList.props('authors')).toHaveLength(5)
    })

    it('does not show pagination in any mode', async () => {
      const wrapper = await mountView()

      const pagination = wrapper.findComponent({ name: 'PaginationControl' })
      expect(pagination.exists()).toBe(false)
    })
  })

  describe('No Search Bar', () => {
    it('does not render search input', async () => {
      const wrapper = await mountView()

      const searchInput = wrapper.find('input[type="text"]')
      expect(searchInput.exists()).toBe(false)
    })
  })

  describe('No Item Count', () => {
    it('does not render item count', async () => {
      const wrapper = await mountView()

      const itemCount = wrapper.findComponent({ name: 'ItemCount' })
      expect(itemCount.exists()).toBe(false)
    })
  })
})
