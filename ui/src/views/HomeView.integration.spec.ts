/**
 * Integration tests for HomeView
 * Tests the complete book browsing flow with filtering, sorting, and pagination
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomeView from './HomeView.vue'
import { useMainStore } from '@/stores/main'
import type { Books } from '@/types'

const mockBooksData: Books = {
  totalCount: 50,
  books: [
    {
      id: 1,
      title: 'Pride and Prejudice',
      author: { id: 'austen-jane', name: 'Jane Austen', bookCount: 6 },
      languages: ['en'],
      popularity: 5,
      coverPath: '/covers/1.jpg',
      lccShelf: 'PR'
    },
    {
      id: 2,
      title: 'Les Misérables',
      author: { id: 'hugo-victor', name: 'Victor Hugo', bookCount: 10 },
      languages: ['fr'],
      popularity: 4,
      coverPath: '/covers/2.jpg',
      lccShelf: 'PQ'
    },
    {
      id: 3,
      title: 'Emma',
      author: { id: 'austen-jane', name: 'Jane Austen', bookCount: 6 },
      languages: ['en'],
      popularity: 3,
      coverPath: '/covers/3.jpg',
      lccShelf: 'PR'
    }
  ]
}

const createManyBooks = (count: number): Books => ({
  totalCount: count,
  books: Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Book ${i + 1}`,
    author: { id: 'author-1', name: 'Author', bookCount: count },
    languages: ['en'],
    popularity: 3,
    coverPath: null,
    lccShelf: 'PR'
  }))
})

describe('HomeView Integration', () => {
  let router: ReturnType<typeof createRouter>
  let store: ReturnType<typeof useMainStore>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useMainStore()
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: HomeView }]
    })
  })

  const mountView = async (mockData: Books = mockBooksData) => {
    vi.spyOn(store, 'fetchBooks').mockResolvedValue(mockData)
    const wrapper = mount(HomeView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads and displays books on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchBooks).toHaveBeenCalledOnce()
      expect(wrapper.text()).toContain('Pride and Prejudice')
      expect(wrapper.text()).toContain('Les Misérables')
      expect(wrapper.text()).toContain('Emma')
    })

    it('shows empty state when no books available', async () => {
      const wrapper = await mountView({ totalCount: 0, books: [] })

      expect(wrapper.findComponent({ name: 'EmptyState' }).exists()).toBe(true)
    })
  })

  describe('View Mode Toggle', () => {
    it('switches between grid and list view', async () => {
      const wrapper = await mountView()

      expect(wrapper.findComponent({ name: 'BookGrid' }).exists()).toBe(true)

      const listButton = wrapper.findAll('button').find((btn) => btn.attributes('value') === 'list')
      expect(listButton).toBeDefined()
      await listButton!.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findComponent({ name: 'BookGrid' }).exists()).toBe(false)
      expect(wrapper.findComponent({ name: 'BookList' }).exists()).toBe(true)
    })
  })

  describe('Language Filtering', () => {
    it('filters books by selected language', async () => {
      const wrapper = await mountView()

      expect(wrapper.text()).toContain('Pride and Prejudice')
      expect(wrapper.text()).toContain('Les Misérables')

      const filters = wrapper.findComponent({ name: 'CollapsibleFilters' })
      await filters.vm.$emit('update:selectedLanguages', ['fr'])
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).not.toContain('Pride and Prejudice')
      expect(wrapper.text()).toContain('Les Misérables')
    })
  })

  describe('Sorting', () => {
    it.each([
      { sortBy: 'popularity', sortOrder: 'desc', expectedFirst: 'Pride and Prejudice' },
      { sortBy: 'title', sortOrder: 'asc', expectedFirst: 'Emma' }
    ] as const)(
      'sorts books by $sortBy $sortOrder',
      async ({ sortBy, sortOrder, expectedFirst }) => {
        const wrapper = await mountView()

        const filters = wrapper.findComponent({ name: 'CollapsibleFilters' })
        await filters.vm.$emit('update:sortBy', sortBy)
        await filters.vm.$emit('update:sortOrder', sortOrder)
        await wrapper.vm.$nextTick()

        const bookCards = wrapper.findAllComponents({ name: 'BookCard' })
        expect(bookCards[0]?.props('book').title).toBe(expectedFirst)
      }
    )
  })

  describe('Pagination', () => {
    it('shows pagination when more than 24 books', async () => {
      const wrapper = await mountView(createManyBooks(30))

      expect(wrapper.findComponent({ name: 'PaginationControl' }).exists()).toBe(true)
    })

    it('does not show pagination for 24 or fewer books', async () => {
      const wrapper = await mountView(createManyBooks(24))

      expect(wrapper.findComponent({ name: 'PaginationControl' }).exists()).toBe(false)
    })
  })

  describe('Item Count Display', () => {
    it('displays correct item count', async () => {
      const wrapper = await mountView()

      const itemCount = wrapper.findComponent({ name: 'ItemCount' })
      expect(itemCount.exists()).toBe(true)
      expect(itemCount.props('current')).toBe(3)
      expect(itemCount.props('total')).toBe(3)
      expect(itemCount.props('type')).toBe('books')
    })
  })
})
