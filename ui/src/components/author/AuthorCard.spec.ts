/**
 * Component tests for AuthorCard
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AuthorCard from './AuthorCard.vue'
import type { AuthorPreview } from '@/types'

// Mock format-utils
vi.mock('@/utils/format-utils', () => ({
  pluralize: (count: number, word: string) => (count === 1 ? word : `${word}s`)
}))

// Mock constants
vi.mock('@/constants/theme', () => ({
  AVATAR_SIZES: {
    CARD: 80
  },
  ICON_SIZES: {
    CARD: 48,
    SMALL: 16
  }
}))

describe('AuthorCard', () => {
  const createAuthor = (overrides?: Partial<AuthorPreview>): AuthorPreview => ({
    id: 'austen-jane',
    name: 'Jane Austen',
    bookCount: 42,
    ...overrides
  })

  describe('Rendering', () => {
    it('renders card with author name and book count', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).exists()).toBe(true)
      expect(wrapper.text()).toContain('Jane Austen')
      expect(wrapper.text()).toContain('42 books')
    })

    it('renders avatar with account icon', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.exists()).toBe(true)
      expect(avatar.props('size')).toBe(80)
      expect(avatar.props('color')).toBe('primary')

      const icons = wrapper.findAllComponents({ name: 'VIcon' })
      const accountIcon = icons.find((icon) => icon.props('icon') === 'mdi-account')
      expect(accountIcon).toBeDefined()
      expect(accountIcon!.props('size')).toBe(48)
    })

    it('renders book icon with count', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const icons = wrapper.findAllComponents({ name: 'VIcon' })
      const bookIcon = icons.find((icon) => icon.props('icon') === 'mdi-book-multiple')
      expect(bookIcon).toBeDefined()
      expect(bookIcon!.props('size')).toBe(16)
    })
  })

  describe('Navigation', () => {
    it('links to author detail page with hover effect', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.props('to')).toBe('/author/austen-jane')
      expect(card.props('hover')).toBe(true)
    })

    it('links to correct author ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ id: 'shakespeare-william' }) }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toBe(
        '/author/shakespeare-william'
      )
    })
  })

  describe('Accessibility', () => {
    it('has aria-label and tabindex for keyboard navigation', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.attributes('aria-label')).toBe('View author: Jane Austen with 42 books')
      expect(card.attributes('tabindex')).toBe('0')
    })
  })

  describe('Book Count Display', () => {
    it.each([
      { count: 1, expected: '1 book', notExpected: 'books' },
      { count: 0, expected: '0 books', notExpected: null },
      { count: 2, expected: '2 books', notExpected: null },
      { count: 150, expected: '150 books', notExpected: null }
    ])('displays "$expected" for count of $count', ({ count, expected, notExpected }) => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ bookCount: count }) }
      })

      expect(wrapper.text()).toContain(expected)
      if (notExpected) {
        expect(wrapper.text()).not.toContain(notExpected)
      }
    })
  })

  describe('Card Structure', () => {
    it('has correct layout classes', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.classes()).toContain('card-full-height')

      const text = wrapper.findComponent({ name: 'VCardText' })
      expect(text.classes()).toContain('text-center')
      expect(text.classes()).toContain('pa-6')

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.classes()).toContain('mb-4')
    })

    it('renders title and subtitle with correct classes', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const title = wrapper.findComponent({ name: 'VCardTitle' })
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Jane Austen')
      expect(title.classes()).toContain('text-wrap')

      const subtitle = wrapper.findComponent({ name: 'VCardSubtitle' })
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.classes()).toContain('mt-2')
    })
  })

  describe('Name Variations', () => {
    it.each([
      'Homer',
      'Johann Wolfgang von Goethe',
      'Brontë, Charlotte',
      "O'Brien, Flann",
      'Saint-Exupéry, Antoine de'
    ])('handles name format: %s', (name) => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ name }) }
      })

      expect(wrapper.text()).toContain(name)
    })
  })

  describe('ID Variations', () => {
    it.each(['homer', 'conan-doyle-arthur', 'author-123', 'author_name_123'])(
      'handles ID format: %s',
      (id) => {
        const wrapper = mount(AuthorCard, {
          props: { author: createAuthor({ id }) }
        })

        expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toBe(`/author/${id}`)
      }
    )
  })

  describe('Edge Cases', () => {
    it('handles extreme book counts', () => {
      const wrapper0 = mount(AuthorCard, {
        props: { author: createAuthor({ bookCount: 0 }) }
      })
      expect(wrapper0.text()).toContain('0 books')

      const wrapper9999 = mount(AuthorCard, {
        props: { author: createAuthor({ bookCount: 9999 }) }
      })
      expect(wrapper9999.text()).toContain('9999')
    })

    it('handles empty name and ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ name: '', id: '' }) }
      })

      expect(wrapper.findComponent({ name: 'VCardTitle' }).text()).toBe('')
      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toBe('/author/')
    })
  })
})
