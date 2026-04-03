/**
 * Integration tests for AuthorListView
 * Tests author browsing with search and pagination
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

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('hasItems')).toBe(false)
    })
  })

  describe('Search Functionality', () => {
    it('filters authors by search query', async () => {
      const wrapper = await mountView()

      expect(wrapper.text()).toContain('Jane Austen')
      expect(wrapper.text()).toContain('Charles Dickens')

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      await listWrapper.vm.$emit('update:searchQuery', 'Jane')
      await wrapper.vm.$nextTick()

      const authorGrid = wrapper.findComponent({ name: 'AuthorGrid' })
      expect(authorGrid.props('authors')).toHaveLength(1)
      expect(authorGrid.props('authors')[0].name).toBe('Jane Austen')
    })

    it('shows all authors when search is cleared', async () => {
      const wrapper = await mountView()

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      await listWrapper.vm.$emit('update:searchQuery', 'Jane')
      await wrapper.vm.$nextTick()

      const authorGrid = wrapper.findComponent({ name: 'AuthorGrid' })
      expect(authorGrid.props('authors')).toHaveLength(1)

      await listWrapper.vm.$emit('update:searchQuery', '')
      await wrapper.vm.$nextTick()

      expect(authorGrid.props('authors')).toHaveLength(5)
    })

    it('handles case-insensitive search', async () => {
      const wrapper = await mountView()

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      await listWrapper.vm.$emit('update:searchQuery', 'DICKENS')
      await wrapper.vm.$nextTick()

      const authorGrid = wrapper.findComponent({ name: 'AuthorGrid' })
      expect(authorGrid.props('authors')).toHaveLength(1)
      expect(authorGrid.props('authors')[0].name).toBe('Charles Dickens')
    })
  })

  describe('Sorting', () => {
    it('sorts authors alphabetically by default', async () => {
      const wrapper = await mountView()

      const authorGrid = wrapper.findComponent({ name: 'AuthorGrid' })
      const authors = authorGrid.props('authors')

      expect(authors[0].name).toBe('Charles Dickens')
      expect(authors[1].name).toBe('Jane Austen')
      expect(authors[2].name).toBe('Mark Twain')
    })
  })

  describe('Pagination', () => {
    const createManyAuthors = () => ({
      totalCount: 30,
      authors: Array.from({ length: 30 }, (_, i) => ({
        id: `author-${i}`,
        name: `Author ${String(i + 1).padStart(2, '0')}`,
        bookCount: 5
      }))
    })

    it('paginates when more than 24 authors', async () => {
      const wrapper = await mountView(createManyAuthors())

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('totalPages')).toBeGreaterThan(1)
    })

    it('resets to page 1 when search query changes', async () => {
      const wrapper = await mountView(createManyAuthors())

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      await listWrapper.vm.$emit('goToPage', 2)
      await wrapper.vm.$nextTick()

      expect(listWrapper.props('currentPage')).toBe(2)

      await listWrapper.vm.$emit('update:searchQuery', 'test')
      await wrapper.vm.$nextTick()

      expect(listWrapper.props('currentPage')).toBe(1)
    })
  })

  describe('Item Count', () => {
    it('displays correct author count', async () => {
      const wrapper = await mountView()

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('currentCount')).toBe(5)
      expect(listWrapper.props('totalCount')).toBe(5)
      expect(listWrapper.props('itemType')).toBe('authors')
    })
  })
})
