/**
 * Component tests for AuthorCard
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AuthorCard from './AuthorCard.vue'
import type { AuthorPreview } from '@/types'

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: unknown) => {
      if (key === 'author.bookCount') {
        const count = typeof params === 'number' ? params : 0
        return count === 1 ? '1 book' : `${count} books`
      }
      if (key === 'author.viewAuthor') {
        const p = params as Record<string, unknown>
        const count = typeof p.n === 'number' ? p.n : 0
        const name = String(p.name || '')
        return `View author: ${name} with ${count} ${count === 1 ? 'book' : 'books'}`
      }
      return key
    }
  })
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  RouterLink: {
    name: 'RouterLink',
    props: ['to'],
    template: '<a :href="to"><slot /></a>'
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
    it('renders card with author name', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      expect(wrapper.find('.author-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('Jane Austen')
    })

    it('renders avatar with account icon', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.exists()).toBe(true)
      expect(avatar.props('size')).toBe(100)
      expect(avatar.props('color')).toBe('primary')

      const icons = wrapper.findAllComponents({ name: 'VIcon' })
      const accountIcon = icons.find((icon) => icon.props('icon') === 'mdi-account')
      expect(accountIcon).toBeDefined()
      expect(accountIcon!.props('size')).toBe(48)
    })
  })

  describe('Navigation', () => {
    it('links to author detail page', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const link = wrapper.find('.author-card')
      expect(link.attributes('to')).toBe('/author/austen-jane')
    })

    it('links to correct author ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ id: 'shakespeare-william' }) }
      })

      expect(wrapper.find('.author-card').attributes('to')).toBe('/author/shakespeare-william')
    })
  })

  describe('Accessibility', () => {
    it('has aria-label for keyboard navigation', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const link = wrapper.find('.author-card')
      expect(link.attributes('aria-label')).toBe('View author: Jane Austen with 42 books')
    })
  })

  describe('Card Structure', () => {
    it('has correct layout classes', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const card = wrapper.find('.author-card')
      expect(card.classes()).toContain('text-decoration-none')

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.classes()).toContain('author-card__avatar')
    })

    it('renders name with correct text', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const name = wrapper.find('.author-card__name')
      expect(name.exists()).toBe(true)
      expect(name.text()).toBe('Jane Austen')
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

        expect(wrapper.find('.author-card').attributes('to')).toBe(`/author/${id}`)
      }
    )
  })

  describe('Edge Cases', () => {
    it('handles empty name and ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ name: '', id: '' }) }
      })

      expect(wrapper.find('.author-card__name').text()).toBe('')
      expect(wrapper.find('.author-card').attributes('to')).toBe('/author/')
    })
  })
})
