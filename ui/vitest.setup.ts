import { config } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createI18n } from 'vue-i18n'

// Mock browser APIs
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.IntersectionObserver = class IntersectionObserver {
  readonly root = null
  readonly rootMargin = ''
  readonly thresholds = []
  
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return []
  }
}

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives
})

// Create i18n instance for tests with minimal English messages
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      common: {
        filterByTitle: 'Filter by {title}',
        clearAllSelections: 'Clear all selections',
        selectAll: 'Select all',
        clear: 'Clear',
        all: 'All',
        filter: 'filter',
        selected: 'selected',
        format: 'Format',
        language: 'Language',
        sort: 'Sort',
        sortPopularity: 'Popularity',
        sortTitle: 'Title'
      },
      author: {
        bookCount: '{n} book | {n} books'
      },
      book: {
        unknown: 'Unknown',
        downloadsCount: '{n} downloads'
      },
      shelf: {
        bookCount: '{n} book | {n} books'
      },
      messages: {
        noBooksForAuthor: 'No books available for this author',
        noBooksInShelf: 'No books in this shelf',
        noBooks: 'No books found',
        noAuthors: 'No authors found',
        noShelves: 'No shelves found',
        noLanguages: 'No languages available',
        noFormats: 'No formats available'
      }
    }
  }
})

// Set global mount options
config.global.plugins = [vuetify, i18n]
