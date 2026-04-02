/**
 * Component tests for LCCShelfCard
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LCCShelfCard from './LCCShelfCard.vue'
import type { LCCShelfPreview } from '@/types'

// Mock format-utils
vi.mock('@/utils/format-utils', () => ({
  pluralize: (count: number, word: string) => (count === 1 ? word : `${word}s`)
}))

// Mock constants
vi.mock('@/constants/theme', () => ({
  AVATAR_SIZES: {
    CARD: 80
  }
}))

describe('LCCShelfCard', () => {
  const createShelf = (overrides?: Partial<LCCShelfPreview>): LCCShelfPreview => ({
    code: 'PR',
    name: 'English literature',
    bookCount: 150,
    ...overrides
  })

  describe('Rendering', () => {
    it('renders card with code, name, and book count', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).exists()).toBe(true)
      expect(wrapper.text()).toContain('PR')
      expect(wrapper.text()).toContain('English literature')
      expect(wrapper.text()).toContain('150 books')
    })

    it('renders avatar with code as bold text', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.exists()).toBe(true)
      expect(avatar.props('size')).toBe(80)
      expect(avatar.props('color')).toBe('primary')
      expect(avatar.classes()).toContain('mb-4')

      const span = avatar.find('span')
      expect(span.text()).toBe('PR')
      expect(span.classes()).toContain('text-h4')
      expect(span.classes()).toContain('font-weight-bold')
    })
  })

  describe('Navigation', () => {
    it('links to shelf detail page with hover effect', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.props('to')).toBe('/lcc-shelf/PR')
      expect(card.props('hover')).toBe(true)
    })

    it('links to correct shelf code', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ code: 'PS' }) }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toBe('/lcc-shelf/PS')
    })
  })

  describe('Accessibility', () => {
    it('has aria-label and tabindex for keyboard navigation', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.attributes('aria-label')).toBe('View LCC shelf: PR with 150 books')
      expect(card.attributes('tabindex')).toBe('0')
    })
  })

  describe('Book Count Display', () => {
    it('displays singular "book" for count of 1', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ bookCount: 1 }) }
      })

      expect(wrapper.text()).toContain('1 book')
      expect(wrapper.text()).not.toContain('books')
    })

    it.each([0, 2, 5000])('displays plural "books" for count of %i', (count) => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ bookCount: count }) }
      })

      expect(wrapper.text()).toContain(`${count} books`)
    })
  })

  describe('Card Structure', () => {
    it('has correct layout classes', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.classes()).toContain('card-full-height')

      const text = wrapper.findComponent({ name: 'VCardText' })
      expect(text.classes()).toContain('text-center')
      expect(text.classes()).toContain('pa-6')
    })

    it('renders title and subtitle with correct classes', () => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf() }
      })

      const title = wrapper.findComponent({ name: 'VCardTitle' })
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('English literature')
      expect(title.classes()).toContain('text-wrap')

      const subtitle = wrapper.findComponent({ name: 'VCardSubtitle' })
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.classes()).toContain('mt-2')
    })
  })

  describe('Name Handling', () => {
    it.each([
      'English literature',
      'American literature in English, 1900-1999',
      'Literature & Arts'
    ])('renders title when name is: %s', (name) => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ name }) }
      })

      expect(wrapper.findComponent({ name: 'VCardTitle' }).exists()).toBe(true)
      expect(wrapper.text()).toContain(name)
    })

    it.each([null, undefined, ''])('does not render title when name is %s', (name) => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ name }) }
      })

      expect(wrapper.findComponent({ name: 'VCardTitle' }).exists()).toBe(false)
    })
  })

  describe('Code Variations', () => {
    it.each(['P', 'PR', 'PRA', 'PR1', 'pr', '', 'P-R'])('handles code format: %s', (code) => {
      const wrapper = mount(LCCShelfCard, {
        props: { shelf: createShelf({ code }) }
      })

      expect(wrapper.findComponent({ name: 'VAvatar' }).text()).toBe(code)
    })
  })

  describe('Edge Cases', () => {
    it('handles extreme book counts', () => {
      const wrapper0 = mount(LCCShelfCard, {
        props: { shelf: createShelf({ bookCount: 0 }) }
      })
      expect(wrapper0.text()).toContain('0 books')

      const wrapper99999 = mount(LCCShelfCard, {
        props: { shelf: createShelf({ bookCount: 99999 }) }
      })
      expect(wrapper99999.text()).toContain('99999 books')
    })

    it('handles shelf with all properties', () => {
      const wrapper = mount(LCCShelfCard, {
        props: {
          shelf: createShelf({
            code: 'PS',
            name: 'American literature',
            bookCount: 250
          })
        }
      })

      expect(wrapper.text()).toContain('PS')
      expect(wrapper.text()).toContain('American literature')
      expect(wrapper.text()).toContain('250 books')
    })

    it('handles shelf without name', () => {
      const wrapper = mount(LCCShelfCard, {
        props: {
          shelf: createShelf({
            code: 'QA',
            name: null,
            bookCount: 100
          })
        }
      })

      expect(wrapper.text()).toContain('QA')
      expect(wrapper.text()).toContain('100 books')
      expect(wrapper.findComponent({ name: 'VCardTitle' }).exists()).toBe(false)
    })
  })
})
