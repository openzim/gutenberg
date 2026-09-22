import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'

import SelectedBooksSection from './SelectedBooksSection.vue'
import type { BookPreview } from '@/types'

const books: BookPreview[] = [
  {
    id: 'first',
    title: 'First three-flame book',
    author: {
      id: 'author-1',
      name: 'First Author',
      firstName: 'First',
      lastName: 'Author',
      bookCount: 1,
      totalPopularity: 10
    },
    languages: ['en'],
    popularity: 10,
    flames: 3,
    coverPath: null,
    primaryCollection: null
  },
  {
    id: 'highest',
    title: 'Highest raw popularity',
    author: {
      id: 'author-2',
      name: 'Second Author',
      firstName: 'Second',
      lastName: 'Author',
      bookCount: 1,
      totalPopularity: 100
    },
    languages: ['en'],
    popularity: 100,
    flames: 3,
    coverPath: null,
    primaryCollection: null
  }
]

describe('SelectedBooksSection', () => {
  it('features the work with the highest raw popularity within a flame bin', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en',
      messages: { en: { home: { mostPopular: 'Most popular' } } }
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: []
    })

    const wrapper = mount(SelectedBooksSection, {
      props: { books },
      global: {
        plugins: [i18n, router],
        stubs: {
          BooksGrid: true,
          FireRating: true,
          SectionHeader: true
        }
      }
    })

    expect(wrapper.find('.featured-book__title').text()).toBe('Highest raw popularity')
  })
})
