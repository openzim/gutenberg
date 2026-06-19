/**
 * Unit tests for SortAndLimitControl component
 * Tests sort selection, limit selection, and view mode toggle
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SortAndLimitControl from './SortAndLimitControl.vue'
import type { SortOption, SortOrder, PageSize } from '@/types'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: unknown) => {
      const translations: Record<string, string> = {
        'common.sortPopularity': 'Popularity',
        'common.sortTitle': 'Title',
        'common.sortAuthor': 'Author',
        'common.showN': 'Show {n}',
        'common.showAll': 'Show All',
        'common.gridView': 'Grid view',
        'common.listView': 'List view'
      }
      let result = translations[key] || key
      if (typeof params === 'number' || typeof params === 'string') {
        result = result.replace('{n}', String(params))
      } else if (params && typeof params === 'object') {
        for (const [k, v] of Object.entries(params as Record<string, unknown>)) {
          result = result.replace(`{${k}}`, String(v))
        }
      }
      return result
    }
  })
}))

const createWrapper = (props: {
  sortBy: SortOption
  sortOrder: SortOrder
  limit: PageSize
  viewMode?: 'grid' | 'list'
  current?: string
  total?: number
  type?: 'books' | 'authors' | 'shelves'
}) =>
  mount(SortAndLimitControl, {
    props: {
      viewMode: 'grid',
      current: '1-20',
      total: 100,
      type: 'books',
      ...props
    }
  })

describe('SortAndLimitControl', () => {
  it('displays item count range', () => {
    const wrapper = createWrapper({
      sortBy: 'title',
      sortOrder: 'asc',
      limit: 20,
      current: '1-20',
      total: 100,
      type: 'books'
    })

    const count = wrapper.find('.sort-and-limit__count')
    expect(count.exists()).toBe(true)
    expect(count.text()).toContain('1-20')
    expect(count.text()).toContain('100')
  })

  it('displays current sort label', () => {
    const wrapper = createWrapper({
      sortBy: 'title',
      sortOrder: 'asc',
      limit: 20
    })

    const label = wrapper.find('.sort-dropdown .dropdown__label')
    expect(label.exists()).toBe(true)
    expect(label.text()).toBe('Title')
  })

  it('displays current limit label', () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 40
    })

    const label = wrapper.find('.limit-dropdown .dropdown__label')
    expect(label.exists()).toBe(true)
    expect(label.text()).toBe('Show 40')
  })

  it('displays show all label correctly', () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 'all'
    })

    const label = wrapper.find('.limit-dropdown .dropdown__label')
    expect(label.exists()).toBe(true)
    expect(label.text()).toBe('Show All')
  })

  it('opens sort dropdown on click', async () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20
    })

    expect(wrapper.find('.sort-dropdown .dropdown__menu').exists()).toBe(false)

    await wrapper.find('.sort-dropdown__trigger').trigger('click')

    expect(wrapper.find('.sort-dropdown .dropdown__menu').exists()).toBe(true)
  })

  it('emits update:sortBy when sort option is selected', async () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20
    })

    await wrapper.find('.sort-dropdown__trigger').trigger('click')
    const items = wrapper.findAll('.sort-dropdown .dropdown__item')
    expect(items.length).toBeGreaterThanOrEqual(2)

    await items[1]!.trigger('click')

    const emitted = wrapper.emitted('update:sortBy')
    expect(emitted).toBeDefined()
    expect(emitted![0]).toEqual(['title'])
  })

  it.each([
    { from: 'popularity', to: 'title', expectedOrder: 'asc' },
    { from: 'title', to: 'popularity', expectedOrder: 'desc' }
  ])(
    'sets $expectedOrder order when switching from $from to $to',
    async ({ from, to, expectedOrder }) => {
      const wrapper = createWrapper({
        sortBy: from as SortOption,
        sortOrder: from === 'popularity' ? 'desc' : 'asc',
        limit: 20
      })

      await wrapper.find('.sort-dropdown__trigger').trigger('click')
      const items = wrapper.findAll('.sort-dropdown .dropdown__item')
      const targetIndex = to === 'title' ? 1 : 0
      await items[targetIndex]!.trigger('click')

      const sortOrderEvent = wrapper.emitted('update:sortOrder')
      expect(sortOrderEvent).toBeDefined()
      expect(sortOrderEvent![0]).toEqual([expectedOrder])
    }
  )

  it('emits update:limit when limit changes', async () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20
    })

    await wrapper.find('.limit-dropdown__trigger').trigger('click')
    const items = wrapper.findAll('.limit-dropdown .dropdown__item')
    expect(items.length).toBeGreaterThanOrEqual(4)

    await items[items.length - 1]!.trigger('click')

    const emitted = wrapper.emitted('update:limit')
    expect(emitted).toBeDefined()
    expect(emitted![0]).toEqual(['all'])
  })

  it('removes document click listener on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20
    })

    wrapper.unmount()

    expect(removeEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function))
    removeEventListenerSpy.mockRestore()
  })

  it('renders view mode toggle buttons', () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20,
      viewMode: 'grid'
    })

    const buttons = wrapper.findAll('.view-mode-toggle__btn')
    expect(buttons.length).toBe(2)
  })

  it('grid button is active when viewMode is grid', () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20,
      viewMode: 'grid'
    })

    const buttons = wrapper.findAll('.view-mode-toggle__btn')
    expect(buttons[0]!.classes()).toContain('view-mode-toggle__btn--active')
    expect(buttons[1]!.classes()).not.toContain('view-mode-toggle__btn--active')
  })

  it('emits update:viewMode when list button is clicked', async () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc',
      limit: 20,
      viewMode: 'grid'
    })

    const buttons = wrapper.findAll('.view-mode-toggle__btn')
    await buttons[1]!.trigger('click')

    const emitted = wrapper.emitted('update:viewMode')
    expect(emitted).toBeDefined()
    expect(emitted![0]).toEqual(['list'])
  })
})
