/**
 * Component tests for ItemCount
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ItemCount from './ItemCount.vue'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, count?: number) => {
      const translations: Record<string, string> = {
        'common.showing': 'Showing',
        'common.of': 'of',
        'itemTypes.books': count === 1 ? 'book' : 'books',
        'itemTypes.authors': count === 1 ? 'author' : 'authors',
        'itemTypes.shelves': count === 1 ? 'shelf' : 'shelves'
      }
      return translations[key] || key
    }
  })
}))

describe('ItemCount', () => {
  describe('Item Types', () => {
    it.each([
      { type: 'books' as const, singular: 'book', plural: 'books' },
      { type: 'authors' as const, singular: 'author', plural: 'authors' },
      { type: 'shelves' as const, singular: 'shelf', plural: 'shelves' }
    ])(
      'displays singular "$singular" for type $type when count is 1',
      ({ type, singular, plural }) => {
        const wrapper = mount(ItemCount, {
          props: { current: 1, total: 1, type }
        })

        expect(wrapper.text()).toContain('1')
        expect(wrapper.text()).toContain(singular)
        expect(wrapper.text()).not.toContain(plural)
      }
    )

    it.each([
      { type: 'books' as const, current: 24, total: 100, plural: 'books' },
      { type: 'books' as const, current: 0, total: 0, plural: 'books' },
      { type: 'books' as const, current: 9999, total: 50000, plural: 'books' },
      { type: 'authors' as const, current: 10, total: 50, plural: 'authors' },
      { type: 'authors' as const, current: 0, total: 0, plural: 'authors' },
      { type: 'shelves' as const, current: 5, total: 20, plural: 'shelves' },
      { type: 'shelves' as const, current: 0, total: 0, plural: 'shelves' }
    ])(
      'displays plural "$plural" for $type with current=$current total=$total',
      ({ type, current, total, plural }) => {
        const wrapper = mount(ItemCount, {
          props: { current, total, type }
        })

        expect(wrapper.text()).toContain(String(current))
        expect(wrapper.text()).toContain(String(total))
        expect(wrapper.text()).toContain(plural)
      }
    )
  })

  describe('Structure', () => {
    it('renders as span with correct classes and order', () => {
      const wrapper = mount(ItemCount, {
        props: { current: 15, total: 75, type: 'authors' }
      })

      const span = wrapper.find('span')
      expect(span.exists()).toBe(true)
      expect(span.classes()).toContain('text-body-2')
      expect(span.classes()).toContain('text-medium-emphasis')

      const text = wrapper.text()
      const showingIndex = text.indexOf('Showing')
      const currentIndex = text.indexOf('15')
      const ofIndex = text.indexOf('of')
      const totalIndex = text.indexOf('75')
      const typeIndex = text.indexOf('authors')

      expect(showingIndex).toBeLessThan(currentIndex)
      expect(currentIndex).toBeLessThan(ofIndex)
      expect(ofIndex).toBeLessThan(totalIndex)
      expect(totalIndex).toBeLessThan(typeIndex)
    })
  })

  describe('Edge Cases', () => {
    it('handles current equal to total', () => {
      const wrapper = mount(ItemCount, {
        props: { current: 42, total: 42, type: 'books' }
      })

      const text = wrapper.text()
      // Verify both current and total appear (even when equal)
      const matches = text.match(/42/g)
      expect(matches).toHaveLength(2)
      expect(text).toContain('of')
    })
  })
})
