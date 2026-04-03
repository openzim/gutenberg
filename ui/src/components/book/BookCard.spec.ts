/**
 * Component tests for BookCard
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BookCard from './BookCard.vue'
import BookCoverImage from '@/components/common/BookCoverImage.vue'
import type { BookPreview } from '@/types'

// Mock format-utils
vi.mock('@/utils/format-utils', () => ({
  getPopularityStars: (popularity: number) => '★'.repeat(popularity) + '☆'.repeat(5 - popularity),
  normalizeImagePath: (path: string) => path
}))

describe('BookCard', () => {
  const createBook = (overrides?: Partial<BookPreview>): BookPreview => ({
    id: 1,
    title: 'Pride and Prejudice',
    author: {
      id: 'austen-jane',
      name: 'Jane Austen',
      bookCount: 6
    },
    languages: ['en'],
    popularity: 5,
    coverPath: '/covers/1.jpg',
    lccShelf: 'PR',
    ...overrides
  })

  describe('Rendering', () => {
    it('renders card with title, author, and cover', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook() }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).exists()).toBe(true)
      expect(wrapper.text()).toContain('Pride and Prejudice')
      expect(wrapper.text()).toContain('Jane Austen')

      const coverImage = wrapper.findComponent(BookCoverImage)
      expect(coverImage.exists()).toBe(true)
      expect(coverImage.props('coverPath')).toBe('/covers/1.jpg')
      expect(coverImage.props('alt')).toBe('Pride and Prejudice cover')
      expect(coverImage.props('size')).toBe(64)
      expect(coverImage.props('height')).toBe('200px')
      expect(coverImage.classes()).toContain('book-cover')
    })
  })

  describe('Navigation', () => {
    it('links to book detail page with hover effect', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.props('to')).toBe('/book/1')
      expect(card.props('hover')).toBe(true)
    })

    it('links to correct book ID', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ id: 42 }) }
      })

      expect(wrapper.findComponent({ name: 'VCard' }).props('to')).toBe('/book/42')
    })
  })

  describe('Accessibility', () => {
    it('has aria-label and tabindex for keyboard navigation', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.attributes('aria-label')).toBe('View book: Pride and Prejudice by Jane Austen')
      expect(card.attributes('tabindex')).toBe('0')
    })

    it('popularity has aria-label', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ popularity: 4 }) }
      })

      const popularitySpan = wrapper.find('.text-warning')
      expect(popularitySpan.attributes('aria-label')).toBe('Popularity: 4 out of 5 stars')
    })
  })

  describe('Popularity Display', () => {
    it.each([
      { popularity: 5, expected: '★★★★★' },
      { popularity: 4, expected: '★★★★☆' },
      { popularity: 3, expected: '★★★☆☆' },
      { popularity: 1, expected: '★☆☆☆☆' },
      { popularity: 0, expected: '☆☆☆☆☆' }
    ])('displays $expected for popularity $popularity', ({ popularity, expected }) => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ popularity }) }
      })

      expect(wrapper.find('.text-warning').text()).toBe(expected)
    })
  })

  describe('Language Chips', () => {
    it('displays single language chip with correct styling', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ languages: ['en'] }) }
      })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.text()).toBe('EN')
      expect(chip.props('size')).toBe('x-small')
      expect(chip.props('variant')).toBe('outlined')
      expect(chip.attributes('aria-label')).toBe('Language: en')
    })

    it('displays multiple language chips in uppercase', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ languages: ['en', 'fr', 'de'] }) }
      })

      const chips = wrapper.findAllComponents({ name: 'VChip' })
      expect(chips).toHaveLength(3)
      expect(chips[0]!.text()).toBe('EN')
      expect(chips[1]!.text()).toBe('FR')
      expect(chips[2]!.text()).toBe('DE')
    })

    it('handles empty languages array', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ languages: [] }) }
      })

      expect(wrapper.findAllComponents({ name: 'VChip' })).toHaveLength(0)
    })
  })

  describe('Card Structure', () => {
    it('has correct layout and components', () => {
      const wrapper = mount(BookCard, {
        props: { book: createBook() }
      })

      const card = wrapper.findComponent({ name: 'VCard' })
      expect(card.classes()).toContain('card-full-height')

      const title = wrapper.findComponent({ name: 'VCardTitle' })
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Pride and Prejudice')

      const subtitle = wrapper.findComponent({ name: 'VCardSubtitle' })
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.text()).toBe('Jane Austen')

      expect(wrapper.findComponent({ name: 'VCardText' }).exists()).toBe(true)
    })
  })

  describe('Data Variations', () => {
    it.each([
      'Emma',
      'The Life and Strange Surprizing Adventures of Robinson Crusoe, of York, Mariner',
      'Alice\'s Adventures in "Wonderland"'
    ])('handles title format: %s', (title) => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ title }) }
      })

      expect(wrapper.text()).toContain(title)
    })

    it.each([
      { id: 'doyle', name: 'Arthur Conan Doyle', bookCount: 10 },
      { id: 'homer', name: 'Homer', bookCount: 2 },
      { id: 'bronte', name: 'Brontë, Charlotte', bookCount: 7 }
    ])('handles author name: $name', (author) => {
      const wrapper = mount(BookCard, {
        props: { book: createBook({ author }) }
      })

      expect(wrapper.text()).toContain(author.name)
    })

    it.each([null, undefined, '/covers/1.jpg', 'covers/1.webp', './images/cover.png'])(
      'handles cover path: %s',
      (coverPath) => {
        const wrapper = mount(BookCard, {
          props: { book: createBook({ coverPath }) }
        })

        const coverImage = wrapper.findComponent(BookCoverImage)
        expect(coverImage.props('coverPath')).toBe(coverPath)
      }
    )
  })

  describe('Edge Cases', () => {
    it('handles extreme book IDs', () => {
      const wrapper0 = mount(BookCard, {
        props: { book: createBook({ id: 0 }) }
      })
      expect(wrapper0.findComponent({ name: 'VCard' }).props('to')).toBe('/book/0')

      const wrapper999999 = mount(BookCard, {
        props: { book: createBook({ id: 999999 }) }
      })
      expect(wrapper999999.findComponent({ name: 'VCard' }).props('to')).toBe('/book/999999')
    })

    it('handles many languages', () => {
      const wrapper = mount(BookCard, {
        props: {
          book: createBook({
            languages: ['en', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'zh', 'ja', 'ar']
          })
        }
      })

      expect(wrapper.findAllComponents({ name: 'VChip' })).toHaveLength(10)
    })
  })
})
