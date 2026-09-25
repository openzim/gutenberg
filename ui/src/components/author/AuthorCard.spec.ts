/**
 * Component tests for AuthorCard
 */

import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import AuthorCard from './AuthorCard.vue'
import type { AuthorPreview } from '@/types'
import { normalizeImagePath } from '@/utils/format-utils'

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
        const bookCount = String(p.bookCount || '')
        const name = String(p.name || '')
        return `View author: ${name} (${bookCount})`
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
    firstName: 'Jane',
    lastName: 'Austen',
    bookCount: 42,
    ...overrides
  })

  const linkTarget = (wrapper: ReturnType<typeof mount>) =>
    wrapper.findComponent({ name: 'RouterLink' }).props('to')

  describe('Rendering', () => {
    it('renders card with author name', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      expect(wrapper.find('.author-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('Jane Austen')
    })

    it('renders portrait image when portraitPath is provided', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ portraitPath: './authors/austen-jane.webp' }) }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.exists()).toBe(true)

      const portrait = avatar.findComponent({ name: 'VImg' })
      expect(portrait.exists()).toBe(true)
      expect(portrait.props('src')).toBe(normalizeImagePath('./authors/austen-jane.webp'))
      expect(portrait.props('cover')).toBe(true)

      const placeholder = portrait.findComponent({ name: 'VIcon' })
      expect(placeholder.exists()).toBe(true)
      expect(placeholder.props('icon')).toBe('mdi-account')
    })

    it('falls back to account icon placeholder when portrait fails to load', async () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ portraitPath: './authors/austen-jane.webp' }) }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.findComponent({ name: 'VImg' }).exists()).toBe(true)

      await avatar.find('img').trigger('error')
      await nextTick()

      expect(avatar.findComponent({ name: 'VImg' }).exists()).toBe(false)
      const icons = avatar.findAllComponents({ name: 'VIcon' })
      expect(icons.find((icon) => icon.props('icon') === 'mdi-account')).toBeDefined()
    })

    it('renders avatar with account icon', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      const avatar = wrapper.findComponent({ name: 'VAvatar' })
      expect(avatar.exists()).toBe(true)
      expect(avatar.props('size')).toBe(48)
      expect(avatar.props('color')).toBe('rgb(var(--v-theme-authorAvatarBgd))')

      const icons = wrapper.findAllComponents({ name: 'VIcon' })
      const accountIcon = icons.find((icon) => icon.props('icon') === 'mdi-account')
      expect(accountIcon).toBeDefined()
      expect(accountIcon!.props('size')).toBe(28)
    })
  })

  describe('Navigation', () => {
    it('links to author detail page', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      expect(linkTarget(wrapper)).toBe('/author/austen-jane')
    })

    it('links to correct author ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ id: 'shakespeare-william' }) }
      })

      expect(linkTarget(wrapper)).toBe('/author/shakespeare-william')
    })
  })

  describe('Accessibility', () => {
    it('has aria-label for keyboard navigation', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor() }
      })

      expect(wrapper.attributes('aria-label')).toBe('View author: Jane Austen (42 books)')
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

        expect(linkTarget(wrapper)).toBe(`/author/${id}`)
      }
    )
  })

  describe('Edge Cases', () => {
    it('handles empty name and ID', () => {
      const wrapper = mount(AuthorCard, {
        props: { author: createAuthor({ name: '', id: '' }) }
      })

      expect(wrapper.find('.author-card__name').text()).toBe('')
      expect(linkTarget(wrapper)).toBe('/author/')
    })
  })
})
