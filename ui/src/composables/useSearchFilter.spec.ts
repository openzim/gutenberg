/**
 * Unit tests for useSearchFilter composable
 * Tests search/filter functionality for filtering items based on text query
 */

import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useSearchFilter } from './useSearchFilter'

interface TestBook {
  title: string
  author: string
  tags: string[]
}

const SAMPLE_BOOKS: TestBook[] = [
  { title: 'Pride and Prejudice', author: 'Jane Austen', tags: ['classic', 'romance'] },
  { title: 'Great Expectations', author: 'Charles Dickens', tags: ['classic', 'drama'] },
  { title: '1984', author: 'George Orwell', tags: ['dystopian', 'political'] }
]

describe('useSearchFilter', () => {
  const createFilter = (searchFields: (item: TestBook) => string[]) => {
    const items = ref([...SAMPLE_BOOKS])
    return { items, ...useSearchFilter(() => items.value, searchFields) }
  }

  it('returns all items when search query is empty', () => {
    const { filteredItems } = createFilter((item) => [item.title])

    expect(filteredItems.value).toEqual(SAMPLE_BOOKS)
  })

  it.each([
    { query: 'pride', field: 'title', expected: 'Pride and Prejudice' },
    { query: 'dickens', field: 'author', expected: 'Charles Dickens' }
  ])('filters items by $field with query "$query"', ({ query, field, expected }) => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title, item.author])

    searchQuery.value = query

    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]![field as keyof TestBook]).toBe(expected)
  })

  it.each([
    { query: 'ORWELL', description: 'case-insensitive' },
    { query: '  1984  ', description: 'trims whitespace' }
  ])('is $description', ({ query }) => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title, item.author])

    searchQuery.value = query

    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.title).toBe('1984')
  })

  it('returns empty array when no matches found', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = 'nonexistent'

    expect(filteredItems.value).toEqual([])
  })

  it('searches across multiple fields including arrays and handles partial matches', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [
      item.title,
      item.author,
      ...item.tags
    ])

    searchQuery.value = 'classic'
    expect(filteredItems.value).toHaveLength(2)

    searchQuery.value = 'exp'
    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.title).toBe('Great Expectations')
  })

  it('reacts to changes in the source items', () => {
    const { items, filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = 'pride'
    expect(filteredItems.value).toHaveLength(1)

    items.value = [...items.value, { title: 'Pride of Lions', author: 'Test Author', tags: [] }]
    expect(filteredItems.value).toHaveLength(2)
  })

  it('handles empty items array', () => {
    const items = ref<TestBook[]>([])
    const { filteredItems, searchQuery } = useSearchFilter(
      () => items.value,
      (item) => [item.title]
    )

    searchQuery.value = 'test'

    expect(filteredItems.value).toEqual([])
  })
})
