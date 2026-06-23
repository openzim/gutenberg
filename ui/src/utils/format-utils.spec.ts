/**
 * Unit tests for format-utils.ts
 * Tests cover formatting functions used throughout the UI for displaying
 * author names, dates, numbers, languages, and other user-facing content.
 */

import { describe, it, expect } from 'vitest'
import {
  formatAuthorLifespan,
  formatDownloads,
  formatLanguages,
  pluralize,
  extractUniqueValues,
  normalizeImagePath
} from './format-utils'

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

describe('formatLanguages', () => {
  it.each([
    { langs: [], expected: '' },
    { langs: ['en'], expected: 'English' },
    { langs: ['fr'], expected: 'French' },
    { langs: ['en', 'fr'], expected: 'English, French' },
    { langs: ['xyz'], expected: 'xyz' }
  ])('formats $langs as "$expected" with default (en) locale', ({ langs, expected }) => {
    expect(formatLanguages(langs)).toBe(expected)
  })

  it('uses uiLocale for translated names', () => {
    expect(formatLanguages(['en'], { uiLocale: 'fr' })).toBe('anglais')
    expect(formatLanguages(['de'], { uiLocale: 'fr' })).toBe('allemand')
  })

  it('falls back to English when locale has no CLDR data', () => {
    expect(formatLanguages(['en'], { uiLocale: 'zzz' })).toBe('English')
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
