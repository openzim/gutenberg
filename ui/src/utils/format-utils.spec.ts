/**
 * Unit tests for format-utils.ts
 * Tests cover formatting functions used throughout the UI for displaying
 * author names, dates, numbers, languages, and other user-facing content.
 */

import { describe, it, expect } from 'vitest'
import {
  formatAuthorName,
  formatAuthorLifespan,
  formatDownloads,
  getPopularityStars,
  formatLanguages,
  pluralize,
  extractUniqueValues,
  normalizeImagePath
} from './format-utils'

describe('formatAuthorName', () => {
  it.each([
    { first: 'Jane', last: 'Austen', expected: 'Jane Austen' },
    { first: 'Charles', last: 'Dickens', expected: 'Charles Dickens' },
    { first: 'José', last: 'García', expected: 'José García' },
    { first: "O'Brien", last: 'Smith', expected: "O'Brien Smith" }
  ])('formats "$first $last" as "$expected"', ({ first, last, expected }) => {
    expect(formatAuthorName(first, last)).toBe(expected)
  })

  it.each([
    { first: null, last: 'Shakespeare', expected: 'Shakespeare' },
    { first: '', last: 'Plato', expected: 'Plato' }
  ])('returns only last name when first name is $first', ({ first, last, expected }) => {
    expect(formatAuthorName(first, last)).toBe(expected)
  })

  it('handles null or empty last name by concatenating as-is', () => {
    expect(formatAuthorName('Madonna', null as unknown as string)).toBe('Madonna null')
    expect(formatAuthorName('Prince', '')).toBe('Prince ')
  })

  it('preserves whitespace without trimming', () => {
    expect(formatAuthorName(' Jane ', ' Austen ')).toBe(' Jane   Austen ')
    expect(formatAuthorName('  ', 'Shakespeare')).toBe('   Shakespeare')
  })
})

describe('formatAuthorLifespan', () => {
  it.each([
    { birth: '1775', death: '1817', expected: '1775 - 1817', description: 'full lifespan' },
    { birth: '1950', death: null, expected: '1950 -', description: 'birth year only' },
    { birth: null, death: '2020', expected: '- 2020', description: 'death year only' },
    { birth: null, death: null, expected: '', description: 'both years null' },
    { birth: '-384', death: '-322', expected: '-384 - -322', description: 'BCE years' },
    {
      birth: 'c. 1564',
      death: '1616',
      expected: 'c. 1564 - 1616',
      description: 'approximate years'
    }
  ])('formats $description', ({ birth, death, expected }) => {
    expect(formatAuthorLifespan(birth, death)).toBe(expected)
  })
})

describe('formatDownloads', () => {
  it.each([
    { value: 0, expected: '0' },
    { value: 1, expected: '1' },
    { value: 999, expected: '999' },
    { value: 1000, expected: '1.0K' },
    { value: 1234, expected: '1.2K' },
    { value: 5500, expected: '5.5K' },
    { value: 999000, expected: '999.0K' },
    { value: 999999, expected: '1000.0K' },
    { value: 1000000, expected: '1.0M' },
    { value: 1234567, expected: '1.2M' },
    { value: 1500000, expected: '1.5M' },
    { value: 1567890, expected: '1.6M' },
    { value: 15000000, expected: '15.0M' }
  ])('formats $value as $expected', ({ value, expected }) => {
    expect(formatDownloads(value)).toBe(expected)
  })
})

describe('getPopularityStars', () => {
  it.each([
    { rating: -1, expected: '☆☆☆☆☆' },
    { rating: 0, expected: '☆☆☆☆☆' },
    { rating: 1, expected: '★☆☆☆☆' },
    { rating: 2, expected: '★★☆☆☆' },
    { rating: 2.9, expected: '★★☆☆☆' },
    { rating: 3, expected: '★★★☆☆' },
    { rating: 4, expected: '★★★★☆' },
    { rating: 4.99, expected: '★★★★☆' },
    { rating: 5, expected: '★★★★★' },
    { rating: 6, expected: '★★★★★' }
  ])('returns $expected for rating $rating', ({ rating, expected }) => {
    expect(getPopularityStars(rating)).toBe(expected)
  })
})

describe('formatLanguages', () => {
  const mockTranslator = {
    t: (key: string) => {
      const translations: Record<string, string> = {
        'languageNames.en': 'English (i18n)',
        'languageNames.fr': 'French (i18n)'
      }
      return translations[key] || key
    },
    te: (key: string) => ['languageNames.en', 'languageNames.fr'].includes(key)
  }

  it.each([
    { langs: [], translator: undefined, expected: '' },
    { langs: ['en'], translator: undefined, expected: 'English' },
    { langs: ['en', 'fr'], translator: undefined, expected: 'English, Français' },
    { langs: ['xyz'], translator: undefined, expected: 'xyz' },
    { langs: ['en'], translator: mockTranslator, expected: 'English (i18n)' },
    { langs: ['en', 'fr'], translator: mockTranslator, expected: 'English (i18n), French (i18n)' }
  ])('formats $langs as "$expected"', ({ langs, translator, expected }) => {
    expect(formatLanguages(langs, translator)).toBe(expected)
  })
})

describe('pluralize', () => {
  it.each([
    { count: 1, word: 'book', plural: undefined, expected: 'book' },
    { count: 1.0, word: 'book', plural: undefined, expected: 'book' },
    { count: 0, word: 'book', plural: undefined, expected: 'books' },
    { count: 2, word: 'book', plural: undefined, expected: 'books' },
    { count: -1, word: 'book', plural: undefined, expected: 'books' },
    { count: 1.5, word: 'book', plural: undefined, expected: 'books' },
    { count: 1, word: 'child', plural: 'children', expected: 'child' },
    { count: 2, word: 'child', plural: 'children', expected: 'children' },
    { count: 5, word: 'person', plural: 'people', expected: 'people' }
  ])('returns "$expected" for $count $word', ({ count, word, plural, expected }) => {
    expect(pluralize(count, word, plural)).toBe(expected)
  })
})

describe('extractUniqueValues', () => {
  it.each([
    {
      items: [],
      expected: [],
      description: 'empty array'
    },
    {
      items: [{ values: [] }, { values: ['a'] }, { values: [] }],
      expected: ['a'],
      description: 'items with empty arrays'
    },
    {
      items: [
        { values: ['fiction', 'classic'] },
        { values: ['fiction', 'modern'] },
        { values: ['classic'] }
      ],
      expected: ['classic', 'fiction', 'modern'],
      description: 'deduplication and sorting'
    },
    {
      items: [{ values: ['Zebra', 'apple', 'Mango'] }],
      expected: ['Mango', 'Zebra', 'apple'],
      description: 'case-sensitive sorting'
    }
  ])('handles $description', ({ items, expected }) => {
    expect(extractUniqueValues(items, (item) => item.values)).toEqual(expected)
  })
})

describe('normalizeImagePath', () => {
  it.each([
    { input: 'image.jpg', expected: './image.jpg', description: 'simple filename' },
    { input: 'path/to/image.png', expected: './path/to/image.png', description: 'path' },
    { input: './image.jpg', expected: './image.jpg', description: 'already prefixed' },
    { input: '', expected: './', description: 'empty string' },
    {
      input: '/absolute/path.jpg',
      expected: './/absolute/path.jpg',
      description: 'absolute path'
    },
    { input: '../image.jpg', expected: './../image.jpg', description: 'relative parent path' }
  ])('handles $description: "$input" -> "$expected"', ({ input, expected }) => {
    expect(normalizeImagePath(input)).toBe(expected)
  })
})
