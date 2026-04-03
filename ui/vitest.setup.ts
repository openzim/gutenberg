import { config } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createI18n } from 'vue-i18n'

// Mock browser APIs
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
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
      },
      languageNames: {
        en: 'English',
        fr: 'French',
        de: 'German',
        es: 'Spanish'
      }
    }
  }
})

// Set global mount options
config.global.plugins = [vuetify, i18n]
