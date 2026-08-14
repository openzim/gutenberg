/**
 * Component tests for CollectionCard
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CollectionCard from './CollectionCard.vue'
import type { CollectionPreview } from '@/types'

// Mock format-utils
vi.mock('@/utils/format-utils', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/utils/format-utils')>()),
  pluralize: (count: number, word: string) => (count === 1 ? word : `${word}s`)
}))

// Mock constants
vi.mock('@/constants/theme', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/constants/theme')>()),
  AVATAR_SIZES: {
    CARD: 80
  }
}))

describe('CollectionCard', () => {
  const createCollection = (overrides?: Partial<CollectionPreview>): CollectionPreview => ({
    id: 'PR',
    name: 'English literature',
    bookCount: 150,
    ...overrides
  })

  describe('Rendering', () => {
    it('renders card with id, name, and book count', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).exists()).toBe(true)
      expect(wrapper.text()).toContain('PR')
      expect(wrapper.text()).toContain('English literature')
      expect(wrapper.text()).toContain('150 books')
    })

    it('renders avatar with id as bold text', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
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
    it('links to collection detail page with hover effect', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.props('to')).toEqual({ path: '/collections', query: { collection: 'PR' } })
      expect(card.props('hover')).toBe(true)
    })

    it('links to correct collection id', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ id: 'PS' }) }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toEqual({
        path: '/collections',
        query: { collection: 'PS' }
      })
    })

    it('keeps reserved characters in the collection query value', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ id: 'A&B#C' }) }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toEqual({
        path: '/collections',
        query: { collection: 'A&B#C' }
      })
    })
  })

  describe('Accessibility', () => {
    it('has aria-label and tabindex for keyboard navigation', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.attributes('aria-label')).toBe('View collection: PR with 150 books')
      expect(card.attributes('tabindex')).toBe('0')
    })
  })

  describe('Book Count Display', () => {
    it('displays singular "book" for count of 1', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ bookCount: 1 }) }
      })

      expect(wrapper.text()).toContain('1 book')
      expect(wrapper.text()).not.toContain('books')
    })

    it.each([0, 2, 5000])('displays plural "books" for count of %i', (count) => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ bookCount: count }) }
      })

      expect(wrapper.text()).toContain(`${count} books`)
    })
  })

  describe('Card Structure', () => {
    it('has correct layout classes', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.classes()).toContain('card-full-height')

      const text = wrapper.findComponent({ name: 'VCardText' })
      expect(text.classes()).toContain('text-center')
      expect(text.classes()).toContain('pa-6')
    })

    it('renders title and subtitle with correct classes', () => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection() }
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
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ name }) }
      })

      expect(wrapper.findComponent({ name: 'VCardTitle' }).exists()).toBe(true)
      expect(wrapper.text()).toContain(name)
    })

    it.each([undefined, ''])('does not render title when name is %s', (name) => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ name }) }
      })

      expect(wrapper.findComponent({ name: 'VCardTitle' }).exists()).toBe(false)
    })
  })

  describe('Code Variations', () => {
    it.each(['P', 'PR', 'PRA', 'PR1', 'pr', '', 'P-R'])('handles id format: %s', (id) => {
      const wrapper = mount(CollectionCard, {
        props: { collection: createCollection({ id }) }
      })

      expect(wrapper.findComponent({ name: 'VAvatar' }).text()).toBe(id)
    })
  })

  describe('Edge Cases', () => {
    it('handles extreme book counts', () => {
      const wrapper0 = mount(CollectionCard, {
        props: { collection: createCollection({ bookCount: 0 }) }
      })
      expect(wrapper0.text()).toContain('0 books')

      const wrapper99999 = mount(CollectionCard, {
        props: { collection: createCollection({ bookCount: 99999 }) }
      })
      expect(wrapper99999.text()).toContain('99999 books')
    })

    it('handles collection with all properties', () => {
      const wrapper = mount(CollectionCard, {
        props: {
          collection: createCollection({
            id: 'PS',
            name: 'American literature',
            bookCount: 250
          })
        }
      })

      expect(wrapper.text()).toContain('PS')
      expect(wrapper.text()).toContain('American literature')
      expect(wrapper.text()).toContain('250 books')
    })

    it('handles collection without name', () => {
      const wrapper = mount(CollectionCard, {
        props: {
          collection: createCollection({
            id: 'QA',
            name: undefined,
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
