/**
 * Integration tests for LCCShelfListView
 * Tests LCC shelf browsing with search and pagination
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LCCShelfListView from './LCCShelfListView.vue'
import { useMainStore } from '@/stores/main'
import type { LCCShelves } from '@/types'

const mockShelvesData: LCCShelves = {
  totalCount: 4,
  shelves: [
    { code: 'PR', name: 'English literature', bookCount: 150 },
    { code: 'PS', name: 'American literature', bookCount: 200 },
    { code: 'PQ', name: 'French literature', bookCount: 100 },
    { code: 'PT', name: 'German literature', bookCount: 80 }
  ]
}

const createManyShelves = (count: number): LCCShelves => ({
  totalCount: count,
  shelves: Array.from({ length: count }, (_, i) => ({
    code: `P${String(i + 1).padStart(3, '0')}`,
    name: `Literature ${i}`,
    bookCount: 50
  }))
})

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

  const mountView = async (mockData: LCCShelves = mockShelvesData) => {
    vi.spyOn(store, 'fetchLCCShelves').mockResolvedValue(mockData)
    const wrapper = mount(LCCShelfListView, {
      global: {
        plugins: [pinia, router]
      }
    })
    await flushPromises()
    return wrapper
  }

  describe('Data Loading', () => {
    it('loads and displays shelves on mount', async () => {
      const wrapper = await mountView()

      expect(store.fetchLCCShelves).toHaveBeenCalledOnce()
      expect(wrapper.text()).toContain('English literature')
      expect(wrapper.text()).toContain('American literature')
      expect(wrapper.text()).toContain('French literature')
    })

    it('shows empty state when no shelves available', async () => {
      const wrapper = await mountView({ totalCount: 0, shelves: [] })

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('hasItems')).toBe(false)
    })
  })

  describe('Search Functionality', () => {
    it.each([
      {
        query: 'English',
        expectedLength: 1,
        expectedField: 'name',
        expectedValue: 'English literature'
      },
      { query: 'PR', expectedLength: 1, expectedField: 'code', expectedValue: 'PR' },
      {
        query: 'AMERICAN',
        expectedLength: 1,
        expectedField: 'name',
        expectedValue: 'American literature'
      }
    ] as const)(
      'filters shelves by "$query"',
      async ({ query, expectedLength, expectedField, expectedValue }) => {
        const wrapper = await mountView()

        const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
        await listWrapper.vm.$emit('update:searchQuery', query)
        await wrapper.vm.$nextTick()

        const shelfGrid = wrapper.findComponent({ name: 'LCCShelfGrid' })
        expect(shelfGrid.props('shelves')).toHaveLength(expectedLength)
        expect(shelfGrid.props('shelves')[0][expectedField]).toBe(expectedValue)
      }
    )
  })

  describe('Sorting', () => {
    it('sorts shelves alphabetically by code by default', async () => {
      const wrapper = await mountView()

      const shelfGrid = wrapper.findComponent({ name: 'LCCShelfGrid' })
      const shelves = shelfGrid.props('shelves')

      expect(shelves[0].code).toBe('PQ')
      expect(shelves[1].code).toBe('PR')
      expect(shelves[2].code).toBe('PS')
      expect(shelves[3].code).toBe('PT')
    })
  })

  describe('Pagination', () => {
    it('paginates when more than 24 shelves', async () => {
      const wrapper = await mountView(createManyShelves(30))

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('totalPages')).toBeGreaterThan(1)
    })

    it('resets to page 1 when search query changes', async () => {
      const wrapper = await mountView(createManyShelves(30))

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
    it('displays correct shelf count', async () => {
      const wrapper = await mountView()

      const listWrapper = wrapper.findComponent({ name: 'ListViewWrapper' })
      expect(listWrapper.props('currentCount')).toBe(4)
      expect(listWrapper.props('totalCount')).toBe(4)
      expect(listWrapper.props('itemType')).toBe('shelves')
    })
  })
})
