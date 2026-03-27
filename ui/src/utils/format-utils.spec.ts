/**
 * Unit tests for format-utils.ts
 * Tests cover formatting functions used throughout the UI for displaying
 * author names, dates, numbers, languages, and other user-facing content.
 */

import { describe, it, expect, vi } from 'vitest'

// Mock vue-i18n before any imports to avoid dependency on actual i18n setup
vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    createI18n: vi.fn(() => ({
      global: {
        t: vi.fn(),
        locale: { value: 'en' }
      }
    })),
    // Mock translation functions with sample language names
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'languageNames.en': 'English',
          'languageNames.fr': 'French',
          'languageNames.de': 'German',
          'languageNames.es': 'Spanish'
        }
        return translations[key] || key
      },
      te: (key: string) => {
        return [
          'languageNames.en',
          'languageNames.fr',
          'languageNames.de',
          'languageNames.es'
        ].includes(key)
      }
    })
  }
})

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
  it('formats full name when both first and last name provided', () => {
    expect(formatAuthorName('Jane', 'Austen')).toBe('Jane Austen')
    expect(formatAuthorName('Charles', 'Dickens')).toBe('Charles Dickens')
  })

  it('returns only last name when first name is null or empty', () => {
    expect(formatAuthorName(null, 'Shakespeare')).toBe('Shakespeare')
    expect(formatAuthorName('', 'Plato')).toBe('Plato')
  })

  it('handles names with special characters', () => {
    expect(formatAuthorName('José', 'García')).toBe('José García')
    expect(formatAuthorName("O'Brien", 'Smith')).toBe("O'Brien Smith")
  })

  it('handles null or empty last name by concatenating as-is', () => {
    // Note: lastName parameter is typed as string (not nullable) in the function signature
    // These tests document actual behavior when null/empty is passed
    expect(formatAuthorName('Madonna', null as unknown as string)).toBe('Madonna null')
    expect(formatAuthorName('Prince', '')).toBe('Prince ')
  })

  it('preserves whitespace without trimming', () => {
    // Function does not trim whitespace
    expect(formatAuthorName(' Jane ', ' Austen ')).toBe(' Jane   Austen ')
    expect(formatAuthorName('  ', 'Shakespeare')).toBe('   Shakespeare')
  })
})

describe('formatAuthorLifespan', () => {
  it('formats full lifespan when both years provided', () => {
    expect(formatAuthorLifespan('1775', '1817')).toBe('1775 - 1817')
  })

  it('formats birth year only when death year is null', () => {
    expect(formatAuthorLifespan('1950', null)).toBe('1950 -')
  })

  it('formats death year only when birth year is null', () => {
    expect(formatAuthorLifespan(null, '2020')).toBe('- 2020')
  })

  it('returns empty string when both years are null', () => {
    expect(formatAuthorLifespan(null, null)).toBe('')
  })

  it('handles special year formats', () => {
    expect(formatAuthorLifespan('-384', '-322')).toBe('-384 - -322')
    expect(formatAuthorLifespan('c. 1564', '1616')).toBe('c. 1564 - 1616')
  })
})

describe('formatDownloads', () => {
  // Tests grouped by magnitude for clarity
  describe('millions', () => {
    it('formats values >= 1M with one decimal place', () => {
      expect(formatDownloads(1000000)).toBe('1.0M')
      expect(formatDownloads(1500000)).toBe('1.5M')
      expect(formatDownloads(15000000)).toBe('15.0M')
    })

    it('rounds to one decimal place', () => {
      expect(formatDownloads(1234567)).toBe('1.2M')
      expect(formatDownloads(1567890)).toBe('1.6M')
    })
  })

  describe('thousands', () => {
    it('formats values >= 1K with one decimal place', () => {
      expect(formatDownloads(1000)).toBe('1.0K')
      expect(formatDownloads(5500)).toBe('5.5K')
      expect(formatDownloads(999000)).toBe('999.0K')
    })

    it('rounds to one decimal place', () => {
      expect(formatDownloads(1234)).toBe('1.2K')
    })
  })

  describe('under 1000', () => {
    it('returns number as string', () => {
      expect(formatDownloads(0)).toBe('0')
      expect(formatDownloads(1)).toBe('1')
      expect(formatDownloads(999)).toBe('999')
    })
  })

  it('handles boundary values correctly', () => {
    expect(formatDownloads(999)).toBe('999')
    expect(formatDownloads(1000)).toBe('1.0K')
    expect(formatDownloads(999999)).toBe('1000.0K')
    expect(formatDownloads(1000000)).toBe('1.0M')
  })
})

describe('getPopularityStars', () => {
  it('returns correct stars for valid ratings 0-5', () => {
    expect(getPopularityStars(0)).toBe('☆☆☆☆☆')
    expect(getPopularityStars(1)).toBe('★☆☆☆☆')
    expect(getPopularityStars(2)).toBe('★★☆☆☆')
    expect(getPopularityStars(3)).toBe('★★★☆☆')
    expect(getPopularityStars(4)).toBe('★★★★☆')
    expect(getPopularityStars(5)).toBe('★★★★★')
  })

  it('clamps values outside 0-5 range', () => {
    expect(getPopularityStars(-1)).toBe('☆☆☆☆☆')
    expect(getPopularityStars(6)).toBe('★★★★★')
  })

  it('floors decimal values', () => {
    expect(getPopularityStars(2.9)).toBe('★★☆☆☆')
    expect(getPopularityStars(4.99)).toBe('★★★★☆')
  })
})

describe('formatLanguages', () => {
  it('formats single language', () => {
    expect(formatLanguages(['en'])).toBe('English')
  })

  it('formats multiple languages with comma separation', () => {
    expect(formatLanguages(['en', 'fr'])).toBe('English, French')
  })

  it('handles empty array', () => {
    expect(formatLanguages([])).toBe('')
  })

  it('handles unknown language codes', () => {
    const result = formatLanguages(['xyz'])
    expect(result).toBe('xyz')
  })
})

describe('pluralize', () => {
  it('returns singular form when count is 1', () => {
    expect(pluralize(1, 'book')).toBe('book')
    expect(pluralize(1.0, 'book')).toBe('book')
  })

  it('returns default plural form (adds "s") when count is not 1', () => {
    expect(pluralize(0, 'book')).toBe('books')
    expect(pluralize(2, 'book')).toBe('books')
    expect(pluralize(-1, 'book')).toBe('books')
    expect(pluralize(1.5, 'book')).toBe('books')
  })

  it('uses custom plural form when provided', () => {
    expect(pluralize(1, 'child', 'children')).toBe('child')
    expect(pluralize(2, 'child', 'children')).toBe('children')
    expect(pluralize(5, 'person', 'people')).toBe('people')
  })
})

describe('extractUniqueValues', () => {
  // Generic utility for extracting and deduplicating array values from objects
  it('extracts, deduplicates, and sorts values', () => {
    const items = [
      { tags: ['fiction', 'classic'] },
      { tags: ['fiction', 'modern'] },
      { tags: ['classic'] }
    ]
    expect(extractUniqueValues(items, (item) => item.tags)).toEqual([
      'classic',
      'fiction',
      'modern'
    ])
  })

  it('handles empty arrays', () => {
    expect(extractUniqueValues<{ values: string[] }>([], (item) => item.values)).toEqual([])

    const items = [{ values: [] }, { values: ['a'] }, { values: [] }]
    expect(extractUniqueValues(items, (item) => item.values)).toEqual(['a'])
  })

  it('sorts case-sensitively', () => {
    const items = [{ values: ['Zebra', 'apple', 'Mango'] }]
    expect(extractUniqueValues(items, (item) => item.values)).toEqual(['Mango', 'Zebra', 'apple'])
  })
})

describe('normalizeImagePath', () => {
  // Ensures image paths work correctly in ZIM file context
  it('adds ./ prefix when not present', () => {
    expect(normalizeImagePath('image.jpg')).toBe('./image.jpg')
    expect(normalizeImagePath('path/to/image.png')).toBe('./path/to/image.png')
  })

  it('does not add ./ prefix when already present', () => {
    expect(normalizeImagePath('./image.jpg')).toBe('./image.jpg')
  })

  it('handles edge cases', () => {
    expect(normalizeImagePath('')).toBe('./')
    expect(normalizeImagePath('/absolute/path.jpg')).toBe('.//absolute/path.jpg')
    expect(normalizeImagePath('../image.jpg')).toBe('./../image.jpg')
  })
})
