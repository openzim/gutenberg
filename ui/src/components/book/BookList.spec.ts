/**
 * Unit tests for BookList component
 * Tests list view display of books
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BookList from './BookList.vue'
import type { BookPreview } from '@/types'

const createWrapper = (books: BookPreview[]) =>
  mount(BookList, {
    props: { books },
    global: {
      stubs: {
        EmptyState: { template: '<div class="empty-state">{{ message }}</div>', props: ['message'] }
      }
    }
  })

const mockBooks: BookPreview[] = [
  {
    id: 1342,
    title: 'Pride and Prejudice',
    author: { id: 'austen-jane', name: 'Austen, Jane', bookCount: 6 },
    languages: ['en'],
    popularity: 5,
    coverPath: './covers/1342.jpg',
    lccShelf: 'PR'
  },
  {
    id: 84,
    title: 'Frankenstein',
    author: { id: 'shelley-mary', name: 'Shelley, Mary', bookCount: 3 },
    languages: ['en', 'fr'],
    popularity: 4,
    coverPath: null,
    lccShelf: 'PR'
  }
]

describe('BookList', () => {
  it('renders list with items displaying title, author, stars, and languages', () => {
    const wrapper = createWrapper(mockBooks)

    expect(wrapper.find('.v-list').exists()).toBe(true)
    expect(wrapper.findAll('.v-list-item')).toHaveLength(2)

    expect(wrapper.text()).toContain('Pride and Prejudice')
    expect(wrapper.text()).toContain('Austen, Jane')
    expect(wrapper.text()).toContain('Frankenstein')
    expect(wrapper.text()).toContain('Shelley, Mary')
    expect(wrapper.text()).toContain('★★★★★')
    expect(wrapper.text()).toContain('★★★★☆')
    expect(wrapper.text()).toContain('EN')
    expect(wrapper.text()).toContain('FR')
  })

  it('limits language display to 2 languages', () => {
    const books = [
      {
        ...mockBooks[0]!,
        languages: ['en', 'fr', 'de', 'es']
      }
    ]
    const wrapper = createWrapper(books)

    const chips = wrapper.findAll('.v-chip')
    expect(chips.length).toBeLessThanOrEqual(2)
  })

  it.each([
    { coverPath: './covers/1342.jpg', hasImage: true, hasIcon: false },
    { coverPath: null, hasImage: false, hasIcon: true }
  ])('renders avatar with coverPath=$coverPath', ({ coverPath, hasImage, hasIcon }) => {
    const books = [{ ...mockBooks[0]!, coverPath }]
    const wrapper = createWrapper(books)

    const avatar = wrapper.find('.v-avatar')
    expect(avatar.exists()).toBe(true)
    expect(avatar.find('.v-img').exists()).toBe(hasImage)
    expect(avatar.find('.v-icon').exists()).toBe(hasIcon)
  })

  it('shows EmptyState when no books', () => {
    const wrapper = createWrapper([])

    expect(wrapper.find('.v-list').exists()).toBe(false)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })
})
